import requests
from requests.exceptions import InvalidSchema, ConnectionError, MissingSchema, Timeout
from urllib.parse import urlparse, urlencode
import os
import tempfile
import magic
import logging


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
    def getLink(linkedTransaction, acceptedTypes, conf, journal):

        log = logging.getLogger(__name__)
        try:
            acc_header = Network.__create_accept_header(acceptedTypes)
            r = Network.__conditional_fetch(linkedTransaction, acc_header, conf)
            name = Network.__save_content(r.text)
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
    def check_link(linkedTransaction, journal, conf):

        log = logging.getLogger(__name__)
        s = urlparse(linkedTransaction.uri).scheme
        if s not in Network.__allowed_schemata:
            raise UrlError(s+" is not an allowed schema")

        try:
            r = requests.head(linkedTransaction.uri, headers={ "user-agent": conf.getProperty("agent") }, timeout = conf.getProperty("time")) #TODO: accept
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

        if linkedTransaction.uri != r.url:
            log.debug("Redirection: "+linkedTransaction.uri+" -> "+r.url)
            linkedTransaction.uri = r.url

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
    def __conditional_fetch(transaction, accept, conf):
        
        if not transaction.isWorthIt(conf):
            logging.getLogger(__name__).debug("Uri not accepted: "+transaction.uri) 
            raise ConditionError
        elif not conf.type_acceptor.mightAccept(transaction.type):
            logging.getLogger(__name__).debug("Content-type not accepted: "+transaction.type+" ("+transaction.uri+")")
            raise ConditionError
        
        else:
            return Network.__fetch_response(transaction, conf.getProperty("agent"), accept, conf.getProperty('timeout'))

    @staticmethod
    def __fetch_response(transaction, agent, accept, time):

        r = None
        head = {"user-agent" : agent, "accept" : accept }
        if transaction.method == 'GET':
            r = requests.get(transaction.uri+Network.__gen_param(transaction), allow_redirects=False, headers = head, data = transaction.data, timeout = time)
        elif transaction.method == 'POST':
            r = requests.post(transaction.uri, allow_redirects=False, headers = head, data = transaction.data, timeout = time)

        transaction.status = r.status_code
        return r

    @staticmethod
    def __gen_param(transaction):
        if transaction.data is not None:
            param = "?"+urlencode(transaction.data)
        else: 
            param = ""
        return param

    @staticmethod
    def __save_content(content):

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content.encode("utf-8"))
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
            for aType in acceptedTypes:
                string += ", "+aType
            return string
        else:
            return ""
