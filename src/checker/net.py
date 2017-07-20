import requests
from requests.exceptions import InvalidSchema, ConnectionError
from requests.exceptions import MissingSchema, Timeout, TooManyRedirects
from urllib.parse import urlparse, urlencode
import os
import tempfile
import magic
import logging
import math
import time
import sys

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


class Network(object):

    __allowed_schemata = set(['http', 'https'])

    @staticmethod
    def testLink(tr, journal, conf, session, acceptedTypes):
        log = logging.getLogger(__name__)

        log.debug("Fetching %s" % (tr.uri))
        log.debug("Data: %s" % (str(tr.data)))

        s = urlparse(tr.uri).scheme
        if s not in Network.__allowed_schemata:
            raise UrlError(s + " is not an allowed schema")

        accept = ",".join(acceptedTypes)
        log.debug("Accept header: %s" % (accept))

        tr.headers["User-Agent"] = conf.getProperty("agent")
        tr.headers["Accept"] = accept

        # if not allowed to send cookies or don't have any, then cookies are
        # None -> should be safe to use them; maybe filter which to use?

        log.debug("Timeout set to: %s" % (str(conf.getProperty("timeout"))))
        attempt = 0
        max_attempts = conf.getProperty("maxAttempts")
        while attempt < max_attempts:
            try:
                log.debug("Requesting")
                r = session.request(tr.method,
                                    tr.uri + Network.__gen_param(tr),
                                    headers=tr.headers,
                                    timeout=conf.getProperty("timeout"),
                                    cookies=tr.cookies,
                                    verify=conf.getProperty("verifyHttps"),
                                    stream=True)
            except TooManyRedirects as e:
                log.exception("Error while downloading: too many redirects", e)
                raise NetworkError("Too many redirects") from e
            except (ConnectionError, Timeout) as e:
                log.warn("Error while downloading: %s" % e)
                if (attempt + 1) < max_attempts:
                    log.info("Retrying!")
                    wait = math.pow(10, attempt)
                    time.sleep(wait)
                else:
                    raise NetworkError("%s attempts failed" %
                                       str(max_attempts)) from e
                attempt = attempt + 1
            else:
                return Network.__process_link(tr, r, journal, log)
        msg = "All %s attempts to get %s failed." % (str(max_attempts),
                                                     tr.uri)
        journal.foundDefect(tr.idno, "neterr", "Network error", msg, 0.9)
        raise NetworkError(msg)

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
        log = logging.getLogger(__name__)
        try:
            with tempfile.NamedTemporaryFile(delete=False,
                                             prefix=conf.getProperty("tmpPrefix"),
                                             suffix=conf.getProperty("tmpSuffix"),
                                             dir=conf.getProperty("tmpDir", "/tmp/")) as tmp:
                Network.__download(transaction, conf, tmp, journal, log)
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
            match, mime = Network.__test_content_type(transaction.type,
                                                      transaction.file)
            if not match:
                journal.foundDefect(transaction.idno, "type-mishmash",
                                    "Declared content-type doesn't match detected one",
                                    "Declared " + transaction.type + ",detected " + mime,
                                    0.3)

    @staticmethod
    def __download(transaction, conf, tmp, journal, log):
            transaction.file = tmp.name
            log.info("Downloading %s" % transaction.uri)
            log.debug("Downloading chunks into %s" % tmp.name)
            limit = conf.getProperty("maxContentLength", sys.maxsize)
            # jde jen o to, ze pokud maxContentLength neni zadana, pak chceme,
            # aby ten limit byl > nez 10 000 000, pri None to hazi vyjimku
            chsize = min(limit, 10000000)
            for chunk in transaction.request.iter_content(chunk_size=chsize):
                if chunk:
                    tmp.write(chunk)
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
    def __test_content_type(ctype, fname):
        mime = magic.from_file(fname, mime=True)
        return (mime == ctype), mime
