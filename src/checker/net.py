import requests
from requests.exceptions import InvalidSchema, ConnectionError, MissingSchema, Timeout
from urllib.parse import urlparse, urlencode
import os
import tempfile
import magic
import logging
import math
import time


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

    __allowed_schemata = ['http', 'https']

    @staticmethod
    def getLink(linkedTransaction, acceptedTypes, conf, journal, session):

        log = logging.getLogger(__name__)
        try:
            acc_header = Network.__create_accept_header(acceptedTypes)
            log.debug("Accept header: "+acc_header)
            r = Network.__conditional_fetch(linkedTransaction, acc_header, conf, session)
            Network.__store_cookies(linkedTransaction, r.cookies, journal)
            name = Network.__save_content(r.text, conf.getProperty("tmpPrefix"), conf.getProperty("tmpSuffix"))
            match, mime = Network.__test_content_type(linkedTransaction.type, name)
            if not match:
                journal.foundDefect(linkedTransaction.idno, "type-mishmash", "Declared content-type doesn't match detected one", "Declared "+linkedTransaction.type+", detected "+mime, 0.5)
            return name
            
        except ConnectionError as e:
            log.debug("Connection error: "+format(e))
            journal.foundDefect(linkedTransaction.srcId, "badlink", "Invalid link", linkedTransaction.uri, 1.0)
            raise NetworkError(e)
        except Timeout as e:
            log.error("Timeout")
            journal.foundDefect(linkedTransaction.srcId, "timeout", "Link timed out", linkedTransaction.uri, 0.9)
            raise NetworkError() from e

    @staticmethod
    def check_link(linkedTransaction, journal, conf, session, verify=False):

        log = logging.getLogger(__name__)
        s = urlparse(linkedTransaction.uri).scheme
        if s not in Network.__allowed_schemata:
            raise UrlError(s+" is not an allowed schema")

        try:
            r = session.head(linkedTransaction.uri, headers={ "user-agent": conf.getProperty("agent") }, timeout = conf.getProperty("time"), verify=verify) #TODO: accept
        except Timeout as e:
            log.error("Timeout")
            journal.foundDefect(linkedTransaction.srcId, "timeout", "Link timed out", linkedTransaction.uri, 0.9)
            raise NetworkError() from e
        except ConnectionError as e:
            log.debug("Connection error: "+format(e))
            journal.foundDefect(linkedTransaction.srcId, "badlink", "Invalid link", linkedTransaction.uri, 1.0)
            raise NetworkError(e) from e

        linkedTransaction.status = r.status_code

        if r.status_code >= 400:
            journal.foundDefect(linkedTransaction.srcId, "badlink", "Invalid link", linkedTransaction.uri, 1.0)
            raise StatusError(r.status_code)

        lst = list(r.headers.keys())
        if 'content-type' in lst:
            ct = r.headers['content-type']
        elif 'Content-Type' in lst:
            ct = r.headers['Content-Type']
        else:
            ct = ''

        if not ct.strip():
            journal.foundDefect(linkedTransaction.idno, "badtype", "Content-type empty", None, 0.5)

        if ';' in ct: #text/html;charset=utf-8 -> text/html
            ct = ct.split(';')[0]

        return ct, r
    
    @staticmethod
    def __conditional_fetch(transaction, accept, conf, session):
        
        if not transaction.isWorthIt(conf):
            logging.getLogger(__name__).debug("Uri not accepted: "+transaction.uri) 
            raise ConditionError
        elif not conf.type_acceptor.mightAccept(transaction.type):
            logging.getLogger(__name__).debug("Content-type not accepted: "+transaction.type+" ("+transaction.uri+")")
            raise ConditionError
        
        else:
            return Network.__fetch_response(transaction, conf.getProperty("agent"), accept, conf.getProperty('timeout'), session, conf.getProperty("verifyHttps"), conf.getProperty("maxAttempts"))

    @staticmethod
    def __fetch_response(transaction, agent, accept, timeout, session, verify=False, max_attempts=3):

        r = None
        head = {"user-agent" : agent, "accept" : accept }
        log = logging.getLogger(__name__)
        log.debug("Fetching "+transaction.uri)
        log.debug("Data: "+str(transaction.data))
        #if not allowed to send cookies or don't have any, then cookies are None -> should be safe to use them; maybe filter which to use?
        attempt = 0
        while attempt < max_attempts:
            try:
                if transaction.method == 'GET':
                    r = session.get(transaction.uri+Network.__gen_param(transaction), allow_redirects=False, headers = head, timeout = timeout, cookies = transaction.cookies, verify=verify)
                elif transaction.method == 'POST':
                    r = session.post(transaction.uri, allow_redirects=False, headers = head, data = transaction.data, timeout = timeout, cookies = transaction.cookies, verify=verify)
            except ConnectionError as e:
                if (attempt + 1) < max_attempts:
                    wait = math.pow(10, attempt)
                    time.sleep(wait)
                else:
                    raise
                attempt = attempt + 1
            except Timeout as e:
                if (attempt + 1) < max_attempts:
                    wait = math.pow(10, attempt)
                    time.sleep(wait)
                else:
                    raise
                attempt = attempt + 1
            else:
                transaction.status = r.status_code

                if transaction.uri != r.url:
                    logging.getLogger(__name__).debug("Redirection: "+transaction.uri+" -> "+r.url)
                    transaction.changePrimaryUri(r.url)

                return r
            return None 

    @staticmethod
    def __gen_param(transaction):
        if transaction.data is not None:
            param = "?"+urlencode(transaction.data)
        else: 
            param = ""
        return param

    @staticmethod
    def __save_content(content, prefix=None, suffix=None):

        with tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix) as tmp:
            tmp.write(content.encode('utf-8'))
            name = tmp.name
        return name

    @staticmethod
    def __test_content_type(ctype, fname):

        mime = magic.from_file(fname, mime=True)
        return (mime == ctype), mime

    @staticmethod
    def __create_accept_header(acceptedTypes):

        #see RFC 2616, section 14.1
        if len(acceptedTypes) > 0:
            string = acceptedTypes[0]
            for aType in acceptedTypes[2:]:
                string += ", "+aType
            return string
        else:
            return ""

    @staticmethod
    def __store_cookies(transaction, cookies, journal):

        for name, value in cookies.items():
            journal.gotCookie(transaction, name, value)
        transaction.cookies = cookies
            
