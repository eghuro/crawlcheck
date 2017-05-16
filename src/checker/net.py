import requests
from requests.exceptions import InvalidSchema, ConnectionError, MissingSchema, Timeout
from urllib.parse import urlparse, urlencode
import os
import tempfile
import magic
import logging
import math
import time

requests.packages.urllib3.disable_warnings()

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


class Network(object):

    __allowed_schemata = set(['http', 'https'])

    @staticmethod
    def testLink(transaction, journal, conf, session, acceptedTypes):
        log = logging.getLogger(__name__)

        log.debug("Fetching %s" % (transaction.uri))
        log.debug("Data: %s" % (str(transaction.data)))

        s = urlparse(transaction.uri).scheme
        if s not in Network.__allowed_schemata:
            raise UrlError(s + " is not an allowed schema")

        accept = ",".join(acceptedTypes)
        log.debug("Accept header: %s" % (accept))

        transaction.headers["User-Agent"] = conf.getProperty("agent")
        transaction.headers["Accept"] = accept

        #if not allowed to send cookies or don't have any, then cookies are None -> should be safe to use them; maybe filter which to use?
        #TODO: cookies handled by session

        log.debug("Timeout set to: %s" % ( str(conf.getProperty("timeout"))))
        attempt = 0
        max_attempts =  conf.getProperty("maxAttempts")
        while attempt < max_attempts:
            try:
                log.debug("Requesting")
                r = session.request(transaction.method,
                                    transaction.uri + Network.__gen_param(transaction), #TODO: factory method on transaction
                                    headers=transaction.headers,
                                    timeout=conf.getProperty("timeout"),
                                    cookies=transaction.cookies,
                                    verify=conf.getProperty("verifyHttps"),
                                    stream=True)#TODO: data
            except (ConnectionError, Timeout) as e:
                log.debug("Error while downloading: %s" % format(e))
                if (attempt + 1) < max_attempts:
                    log.warn("Failed to get %s, retrying!" % transaction.uri)
                    wait = math.pow(10, attempt)
                    time.sleep(wait)
                else:
                    raise NetworkError("%s attempts failed" % str(max_attempts)) from e
                attempt = attempt + 1
            else:
                return Network.__process_link(transaction, r, journal, log)
        msg = "All %s attempts to get %s failed." % (str(max_attempts), transaction.uri)
        journal.foundDefect(transaction.idno, "neterr", "Network error", msg, 0.9)
        raise NetworkError(msg)


    @staticmethod
    def __process_link(transaction, r, journal, log):
        transaction.status = r.status_code

        if r.status_code >= 400:
            journal.foundDefect(transaction.srcId, "badlink", "Invalid link", transaction.uri, 1.0)
            raise StatusError(r.status_code)

        if transaction.uri != r.url:
            log.debug("Redirection: %s -> %s" % (transaction.uri, r.url))
            transaction.changePrimaryUri(r.url)

        transaction.type = Network.__getCT(r, journal)
        Network.__store_cookies(transaction, r.cookies, journal)

        return r


    @staticmethod
    def __getCT(r, journal):
        if 'content-type' in r.headers:
            ct = r.headers['content-type']
        elif 'Content-Type' in r.headers:
            ct = r.headers['Content-Type']
        else:
            ct = ''

        if not ct.strip():
            journal.foundDefect(transaction.idno, "badtype", "Content-type empty", None, 0.5)

        if ';' in ct: #text/html;charset=utf-8 -> text/html
            ct = ct.split(';')[0]

        return ct


    @staticmethod
    def getContent(transaction, conf, journal):
        log = logging.getLogger(__name__)
        try:
            with tempfile.NamedTemporaryFile(delete=False,
                                             prefix=conf.getProperty("tmpPrefix"),
                                             suffix=conf.getProperty("tmpSuffix")) as tmp:
                Network.__download(transaction, conf, tmp, journal, log)
        except ConnectionError as e:
            log.debug("Connection error: %s" % (format(e)))
            journal.foundDefect(transaction.srcId, "badlink", "Invalid link", transaction.uri, 1.0)
            raise NetworkError from e
        except Timeout as e:
            log.error("Timeout")
            journal.foundDefect(transaction.srcId, "timeout", "Link timed out", transaction.uri, 0.9)
            raise NetworkError() from e
        else:
            match, mime = Network.__test_content_type(transaction.type, transaction.file)
            if not match:
                journal.foundDefect(transaction.idno, "type-mishmash", "Declared content-type doesn't match detected one", "Declared "+transaction.type+", detected "+mime, 0.3)

    @staticmethod
    def __download(transaction, conf, tmp, journal, log):
            transaction.file = tmp.name
            log.info("Downloading %s" % transaction.uri)
            log.debug("Downloading chunks into %s" % tmp.name)
            chsize = min(conf.getProperty("maxContentLength"), 10000000)
            for chunk in transaction.request.iter_content(chunk_size=chsize):
                if chunk:
                    tmp.write(chunk)
            log.debug("%s downloaded." % transaction.uri)


    @staticmethod
    def __gen_param(transaction):
        if (transaction.data is not None) and (len(transaction.data) > 0) and (transaction.method in set(['GET', 'HEAD'])):
            param = "?"+urlencode(transaction.data)
        else: 
            param = ""
        return param

    @staticmethod
    def __store_cookies(transaction, cookies, journal):
        for name, value in cookies.items():
            journal.gotCookie(transaction, name, value)
        transaction.cookies = cookies

    @staticmethod
    def __test_content_type(ctype, fname):
        mime = magic.from_file(fname, mime=True)
        return (mime == ctype), mime
