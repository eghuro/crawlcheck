import requests
from requests.exceptions import InvalidSchema, ConnectionError, MissingSchema
from urlparse import urlparse
import os
import tempfile
import magic


class NetworkError(Exception):
    pass


class UrlError(Exception):
    pass


class StatusError(NetworkError):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Network(object):

    __allowed_schemas = ['http', 'https']

    @staticmethod
    def getLink(srcTransaction, acceptedTypes, conf):
    
        s = urlparse(srcTransaction.uri).scheme
        if s not in Network.__allowed_schemas:
            raise UrlError(s)

        try:
            acc_header = Network.__create_accept_header(acceptedTypes)

            ct = Network.__check_headers(srcTransaction, conf.journal, conf.user_agent, acc_header)
            r = Network.__conditional_fetch(ct, srcTransaction, acc_header, conf)
            name = Network.__save_content(r.text)
            match, mime = Network.__test_content_type(ct, name)
            if not match:
                journal.foundDefect(srcTransaction, "type-mishmash", mime)
            return r, name
            
        except ConnectionError as e:
            print("Connection error: {0}", format(e))
            raise NetworkError(e)
        except StatusError:
            print("Status error: {0}", format(e))
            raise
        except MissingSchema as e:
            print("Missing schema")
            raise NetworkError(e)
        except InvalidSchema as e:
            print("Invalid schema")
            raise NetworkError(e)
     
     
    @staticmethod
    def __check_headers(srcTransaction, journal, agent, accept):
        
        r = requests.head(srcTransaction.uri, headers={ "user-agent": agent, "accept":  accept})
        if r.status_code >= 400:
            journal.foundDefect(srcTransaction, "badlink", url)
            raise StatusError(r.status_code)

        if 'content-type' in r.headers.keys():
            ct = r.headers['content-type']
        elif 'Content-Type' in r.headers.keys():
            ct = r.headers['Content-Type']
        else:
            ct = ''

        if not ct.strip():
            journal.foundDefect(srcTransaction, "badtype", url)
        return ct
    
    @staticmethod
    def __conditional_fetch(ct, transaction, accept, conf):
        
        type_condition = conf.type_acceptor.mightAccept(ct)
        prefix_condition = conf.uri_acceptor.mightAccept(transaction.uri)
        reverse_striped_uri = transaction.getStripedUri()[::-1] #odrizne cestu a zrotuje
        suffix_condition =  conf.suffix_acceptor.mightAccept(reverse_striped_uri) #config loader jiz zrotoval kazdou hodnotu

        if not (prefix_condition or suffix_condition):
            print("Uri not accepted: "+transaction.uri)
            raise NetworkError
        
        elif not type_condition:
            print("Content-type not accepted: "+ct+" ("+transaction.uri+")")
            raise NetworkError
        
        else:
            return fetch_response(transaction.uri, conf.agent)

    @staticmethod
    def fetch_response(url, agent, accept):
        
        r = requests.get(url, allow_redirects=False, headers = {"user-agent" : agent, "accept" : accept })
        return r

    @staticmethod
    def __save_content(content):

        with tempfile.TemporaryFile() as tmp:
            tmp.write(content)
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
