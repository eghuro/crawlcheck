import requests
from requests.exceptions import InvalidSchema, ConnectionError, MissingSchema
from core import Defect
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
    def getLink(urlToFetch, srcTransaction, journal, agent, acceptedTypes):
    
        s = urlparse(urlToFetch).scheme
        if s not in Network.__allowed_schemas:
            raise UrlError(s)

        try:
            acc = Network.create_accept_header(urlToFetch, acceptedTypes)
            ct = Network.check_headers(urlToFetch, srcTransaction, journal, agent, acc)
            r = Network.conditional_fetch(ct, url, agent, acc)
            name = save_content(r.text)
            match, mime = test_content_type(ct, name)
            if not match:
                journal.foundDefect(srcTransaction, Defect("type-mishmash", mime))
            return r, name
            
        except InvalidSchema as e:
            print("Invalid schema")
            raise NetworkError(e)
        except ConnectionError as e:
            print("Connection error: {0}", format(e))
            raise NetworkError(e)
        except MissingSchema as e:
            print("Missing schema")
            raise NetworkError(e)
        except StatusError:
            print("Status error")
            raise
     
     
    @staticmethod
    def check_headers(url, srcTransaction, journal, agent, accept):
        
        r = requests.head(url, headers={ "user-agent": agent, "accept":  accept})
        if r.status_code >= 400:
            journal.foundDefect(srcTransaction, Defect("badlink", url))
            raise StatusError(r.status_code)

        if 'content-type' in r.headers.keys():
            ct = r.headers['content-type']
        elif 'Content-Type' in r.headers.keys():
            ct = r.headers['Content-Type']
        else:
            ct = ''

        if not ct.strip():
            journal.foundDefect(srcTransaction, Defect("badtype", url))
        return ct
    
    @staticmethod
    def conditional_fetch(ct, url, agent, accept):
        
        type_condition = getMaxPrefix(ct) in self.types
        prefix_condition = getMaxPrefixUri(url) in self.uris

        if not prefix_condition:
            print("Uri not accepted: "+url)
            raise NetworkError
        
        elif not type_condition:
            print("Content-type not accepted: "+ct+" ("+url+")")
            raise NetworkError
        
        else:
            return fetch_response(url, agent)

    @staticmethod
    def fetch_response(url, agent, accept):
        
        r = requests.get(url, allow_redirects=False, headers = {"user-agent" : agent, "accept" : accept })
        return r
    
    @staticmethod
    def getMaxPrefix(self, ctype):

        prefList = self.trie.prefixes(unicode(ctype, encoding="utf-8"))
        if len(prefList) > 0:
            return prefList[-1]
        else:
            return ctype

    @staticmethod
    def getMaxPrefixUri(self, uri):
        
        prefList = self.uriTrie.prefixes(uri)
        if len(prefList) > 0:
            return prefList[-1]
        else:
            return uri

    @staticmethod
    def save_content(self, content):
        with tempfile.TemporaryFile() as tmp:
            tmp.write(content)
            name = tmp.name
        return name

    @staticmethod
    def test_content_type(self, ctype, fname):
        mime = magic.from_file(fname, mime=True)
        return (mime == ctype), mime

    @staticmethod
    def create_accept_header(self, forUrl, acceptedTypes):
        #see RFC 2616, section 14.1
        string = ""
        for aType in acceptedTypes:
            string += ", "+aType
        return string
