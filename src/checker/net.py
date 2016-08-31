import requests
from requests.exceptions import InvalidSchema, ConnectionError, MissingSchema
from urllib.parse import urlparse
import os
import tempfile
import magic
import logging


class NetworkError(Exception):
    pass


class UrlError(Exception):
    pass


class ConditionError(Exception):
    pass


class StatusError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Network(object):

    __allowed_schemas = ['http', 'https']

    @staticmethod
    def getLink(linkedTransaction, acceptedTypes, conf, journal):
    
        s = urlparse(linkedTransaction.uri).scheme
        if s not in Network.__allowed_schemas:
            raise UrlError(s)

        log = logging.getLogger()
        try:
            acc_header = Network.__create_accept_header(acceptedTypes)

            ct = str(Network.__check_headers(linkedTransaction, journal, conf.user_agent, acc_header, conf.max_content))
            r = Network.__conditional_fetch(ct, linkedTransaction, acc_header, conf)
            name = Network.__save_content(r.text)
            match, mime = Network.__test_content_type(ct, name)
            if not match:
                journal.foundDefect(linkedTransaction.idno, "type-mishmash", "Declared content-type doesn't match detected one", "Declared "+ct+", detected "+mime, 0.5)
            return ct, name
            
        except ConnectionError as e:
            log.debug("Connection error: "+format(e))
            raise NetworkError(e)
        except StatusError as e:
            log.debug("Status error: "+format(e))
            raise
        except MissingSchema as e:
            log.debug("Missing schema")
            raise NetworkError(e)
        except InvalidSchema as e:
            log.debug("Invalid schema")
            raise NetworkError(e)
     
     
    @staticmethod
    def __check_headers(linkedTransaction, journal, agent, accept, max_content):
        
        r = requests.head(linkedTransaction.uri, headers={ "user-agent": agent, "accept":  accept})
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
            journal.foundDefect(srcTransaction.idno, "badtype", "Content-type empty", None, 0.5)

        if 'Content-Length' in lst:
            conlen = r.headers['Content-Length']
            if max_content is not None:
                if conlen > max_content:
                    log.warning("Content length too large for "+linkedTransaction.uri+" (got: "+conlen+", limit: "+conf.max_content+") Skipping download.")
                    raise ConditionError("Content length too large")

        #TODO: custom HTTP header filters here?

        return ct
    
    @staticmethod
    def __conditional_fetch(ct, transaction, accept, conf):
        
        if not conf.type_acceptor.mightAccept(ct): #zbyle podminky jiz overeny
            logging.getLogger().debug("Content-type not accepted: "+ct+" ("+transaction.uri+")")
            raise ConditionError
        
        else:
            return Network.fetch_response(transaction.uri, conf.user_agent, accept)

    @staticmethod
    def fetch_response(url, agent, accept):
        
        r = requests.get(url, allow_redirects=False, headers = {"user-agent" : agent, "accept" : accept })
        return r

    @staticmethod
    def __save_content(content):

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content.encode("utf-8"))
            name = tmp.name
        return name

    @staticmethod
    def __test_content_type(ctype, fname):

        mime = magic.from_file(fname, mime=True)
        if ';' in ctype: #text/html;charset=utf-8 -> text/html
            ctype = ctype.split(';')[0]
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
