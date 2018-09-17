import requests
from requests.exceptions import InvalidSchema, ConnectionError, SSLError
from requests.exceptions import MissingSchema, Timeout, TooManyRedirects
from urllib.parse import urlparse, urlencode
import os
import backoff
import tempfile
import magic
import logging
import math
import time
import sys
import redis
import uuid


# We handle and log exceptions from libraries.
# This is to prevent libraries to write their messages to the log.
requests.packages.urllib3.disable_warnings()
logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


class NetworkError(Exception):
    pass


class ConditionError(Exception):
    pass


class UrlError(ConditionError):
    pass


class StatusError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def lookup_max_tries():
    return Network.max_tries

def lookup_timeout():
    return Network.max_tries * Network.timeout

def giveup(details):
    msg = "All %s attempts to get %s failed.".format(**details) # (str(max_attempts))
    Network.journal.foundDefect(Network.idno, "neterr", "Network error", msg, 0.9)
    raise NetworkError(msg) from sys.exc_info()[1]

class Network(object):

    __allowed_schemata = set(['http', 'https'])
    max_tries = 1
    journal = None

    @staticmethod
    def __check_schema(uri):
        s = urlparse(uri).scheme
        if s not in Network.__allowed_schemata:
            raise UrlError(s + " is not an allowed schema")

    @staticmethod
    def testLink(tr, journal, conf, session, acceptedTypes):
        """Initiate a connection for the transaction. Read the headers."""

        log = logging.getLogger(__name__)

        log.debug("Fetching %s" % (tr.uri))
        log.debug("Data: %s" % (str(tr.data)))

        Network.__check_schema(tr.uri)

        accept = ",".join(acceptedTypes)
        log.debug("Accept header: %s" % (accept))

        tr.headers["User-Agent"] = conf.getProperty("agent")
        tr.headers["Accept"] = accept

        log.debug("Timeout set to: %s" % (str(conf.getProperty("timeout"))))
        Network.max_tries = conf.getProperty("maxAttempts")
        Network.timeout = conf.getProperty("timeout")
        return Network.__do_request(tr, conf, log, journal, session)


    @staticmethod
    @backoff.on_exception(backoff.expo, (ConnectionError, Timeout),
                          max_tries=lookup_max_tries,
                          max_time=lookup_timeout,
                          on_giveup=giveup)
    def __do_request(tr, conf, log, journal, session):
        Network.journal = journal
        try:
            log.debug("Requesting")
            Network.idno = tr.idno
            r = session.request(tr.method,
                                tr.uri + Network.__gen_param(tr),
                                headers=tr.headers,
                                #timeout=conf.getProperty("timeout"),
                                cookies=tr.cookies,
                                verify=conf.getProperty("verifyHttps"),
                                stream=True)
        except TooManyRedirects as e:
            Network.journal = None
            log.exception("Error while downloading: too many redirects", e)
            raise NetworkError("Too many redirects") from e
        except SSLError as e:
            journal.foundDefect(transaction.srcId, "sslverify", "SSL verification failed", str(e), 0.9)
            raise
        else:
            Network.journal = None
            return Network.__process_link(tr, r, journal, log)

    @staticmethod
    def __process_link(transaction, r, journal, log):
        transaction.status = r.status_code

        if r.status_code != requests.codes.ok:
            journal.foundDefect(transaction.srcId, "badlink", "Invalid link",
                                transaction.uri, 1.0)
            raise StatusError(r.status_code)

        if transaction.uri != r.url:
            log.debug("Redirection: %s -> %s" % (transaction.uri, r.url))
            transaction.changePrimaryUri(r.url)

        transaction.type = Network.__getCT(r, journal, transaction.idno)
        Network.__store_cookies(transaction, r.cookies, journal)

        return r

    @staticmethod
    def __getCT(r, journal, idno):
        if 'content-type' in r.headers:
            ct = r.headers['content-type']
        elif 'Content-Type' in r.headers:
            ct = r.headers['Content-Type']
        else:
            ct = ''

        if not ct.strip():
            journal.foundDefect(idno, "badtype", "Content-type empty", None,
                                0.5)

        if ';' in ct:  # text/html;charset=utf-8 -> text/html
            ct = ct.split(';')[0]

        return ct

    @staticmethod
    def getContent(transaction, conf, journal):
        """
        Finish downloading body of a transaction and store it into a temporary
        file.
        """

        log = logging.getLogger(__name__)
        try:
            #with tempfile.NamedTemporaryFile(delete=False,
            #                                 prefix=conf.getProperty("tmpPrefix"),
            #                                 suffix=conf.getProperty("tmpSuffix"),
            #                                 dir=conf.getProperty("tmpDir", "/tmp/")) as tmp:
            Network.__download(transaction, conf, journal, log)
        except ConnectionError as e:
            log.debug("Connection error: %s" % (format(e)))
            journal.foundDefect(transaction.srcId, "badlink", "Invalid link",
                                transaction.uri, 1.0)
            raise NetworkError from e
        except Timeout as e:
            log.error("Timeout")
            journal.foundDefect(transaction.srcId, "timeout",
                                "Link timed out", transaction.uri, 0.9)
            raise NetworkError() from e
        else:
            red = redis.StrictRedis(host=conf.getProperty('redisHost', 'localhost'), port=conf.getProperty('redisPort', 6379), db=conf.getProperty('redisDb', 0)) 
            match, mime = Network.__test_content_type(transaction.type,
                                                      transaction.file, red)
            if not match:
                journal.foundDefect(transaction.idno, "type-mishmash",
                                    "Declared content-type doesn't match detected one",
                                    "Declared " + transaction.type + ",detected " + mime,
                                    0.3)

    @staticmethod
    def __download(transaction, conf, journal, log):
            MAX_CHSIZE = 10000000
            key = str(uuid.uuid4())
            red = redis.StrictRedis(host=conf.getProperty('redisHost', 'localhost'), port=conf.getProperty('redisPort', 6379), db=conf.getProperty('redisDb', 0)) 
            transaction.file = key
            #transaction.file = tmp.name
            log.info("Downloading %s" % transaction.uri)
            log.debug("Downloading chunks into redis key %s" % key)
            limit = conf.getProperty("maxContentLength", sys.maxsize)
            # Note that the default value here is sys.maxsize.
            # This is to handle the case when maxContentLength is not set.
            # In that case want the limit to be greater than MAX_CHSIZE.
            # If we don't specify our default value, it would be None.
            # But limit cannot be None, it would cause exception in min call.
            chsize = min(limit, MAX_CHSIZE)

            inserted = 0
            for chunk in transaction.request.iter_content(chunk_size=chsize):
                if chunk:
                    red.append(key, chunk)
                    inserted = inserted + len(chunk)
                    #tmp.write(chunk)
            red.expire(key, conf.getProperty('redisExpireContent', 10))
            transaction.size = inserted
            log.debug("%s downloaded." % transaction.uri)

    @staticmethod
    def __gen_param(transaction):
        if (transaction.data is not None) and \
           (len(transaction.data) > 0) and \
           (transaction.method in set(['GET', 'HEAD'])):
            param = "?"+urlencode(transaction.data)
        else:
            param = ""
        return param

    @staticmethod
    def __store_cookies(transaction, cookies, journal):
        for cookie in cookies:
            name = cookie.name
            value = cookie.value
            path = cookie.path
            secure = cookie.secure
            httpOnly = cookie.has_nonstandard_attr('httpOnly')
            journal.gotCookie(transaction, name, value, secure, httpOnly, path)
        transaction.cookies = cookies

    @staticmethod
    def __test_content_type(ctype, fname, red):
        mime = magic.from_buffer(red.get(fname), mime=True)
        return (mime == ctype), mime
