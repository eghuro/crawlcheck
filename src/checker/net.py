import requests
from requests.exceptions import InvalidSchema, ConnectionError, MissingSchema


class NetworkError(Exception):
    pass

class StatusError(NetworkError):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Network(object):

    @staticmethod
    def getLink(url, srcId, db):
    
        try:
            ct = Network.check_headers(url, srcId, db)
            return Network.conditional_fetch(ct, url)
            
        except InvalidSchema as e:
            print("Invalid schema")
            raise NetworkError(e)
        except ConnectionError as e:
            print("Connection error")
            raise NetworkError(e)
        except MissingSchema as e:
            print("Missing schema")
            raise NetworkError(e)
        except StatusError:
            print("Status error")
            raise
     
     
    @staticmethod
    def check_headers(url, srcId, database):
        
        r = requests.head(url)
        if r.status_code >= 400:
            database.setDefect(srcId, "badlink", 0, url)
            raise StatusError(r.status_code)

        if 'content-type' in r.headers.keys():
            ct = r.headers['content-type']
        elif 'Content-Type' in r.headers.keys():
            ct = r.headers['Content-Type']
        else:
            ct = ''

        if not ct.strip():
            database.setDefect(reqId, "badtype", 0, url)
        return ct
    
    @staticmethod
    def conditional_fetch(ct, url):
        
        type_condition = getMaxPrefix(ct) in self.types
        prefix_condition = getMaxPrefixUri(url) in self.uris

        if not prefix_condition:
            print("Uri not accepted: "+url)
            raise NetworkError
        
        elif not type_condition:
            print("Content-type not accepted: "+ct+" ("+url+")")
            raise NetworkError
        
        else:
            return fetch_response(url, reqId, ct)

    @staticmethod
    def fetch_response(url, ct):
        
        r = requests.get(url, allow_redirects=False)
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
