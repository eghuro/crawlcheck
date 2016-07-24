from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
from requests.exceptions import InvalidSchema
from requests.exceptions import ConnectionError
from requests.exceptions import MissingSchema
import requests
from urlparse import urlparse, parse_qs, urljoin
import urllib
import marisa_trie


class StatusError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class LinksFinder(IPlugin):

    def __init__(self):
        self.database = None
        self.types = None
        self.trie = None
        self.uris = None
        self.uriTrie = None
        self.maxDepth = 0  # unlimited
        self.depth = -1

    def setDb(self, DB):
        self.database = DB

    def setTypes(self, types):
        self.types = types
        self.trie = marisa_trie.Trie(types)

    def setUris(self, uris):
        self.uris = uris
        self.uriTrie = marisa_trie.Trie(uris)

    def setDepth(self, depth):
        self.depth = depth

    def setMaxDepth(self, maxDepth):
        self.maxDepth = maxDepth

    def check(self, transactionId, content):
        """ Najde tagy <a>, <link>, <img>, <iframe>, <frame>,
            vybere atribut href, resp. src, ulozi jako odkazy,
            stahne obsah jako dalsi transakci - pritom kontroluje,
            zda se stahovani vyplati - tj. ze obsah bude kontrolovan.
        """
        soup = BeautifulSoup(content, 'html.parser')
        uri = self.database.getUri(transactionId)

        self.checkType(soup, uri, ['a', 'link'], 'href', transactionId)
        self.checkType(soup, uri, ['img', 'iframe', 'frame'], 'src', transactionId)

        return

    def checkType(self, soup, uri, tagL, attr, transactionId):
        if attr == 'href':
            self.make_links_absolute(soup, uri, tagL)
        else:
            self.make_sources_absolute(soup, uri, tagL)

        images = soup.find_all(tagL)

        self.check_links(images, transactionId, attr)
        return

    def getId(self):
        return "linksFinder"

    def getLink(self, url, reqId, srcId):
        try:
            ct = self.check_headers(url, srcId, reqId)
            self.conditional_fetch(ct, url, reqId)
        except InvalidSchema:
            print("Invalid schema")
            self.database.setFinished(reqId)
        except ConnectionError:
            print("Connection error")
            self.database.setFinished(reqId)
        except MissingSchema:
            print("Missing schema")
            self.database.setFinished(reqId)
        except StatusError:
            self.database.setFinished(reqId)

    def check_headers(self, url, srcId, reqId):
        r = requests.head(url)
        if r.status_code >= 400:
            self.database.setDefect(srcId, "badlink", 0, url)
            raise StatusError(r.status_code)

        if 'content-type' in r.headers.keys():
            ct = r.headers['content-type']
        elif 'Content-Type' in r.headers.keys():
            ct = r.headers['Content-Type']
        else:
            ct = ''

        if not ct.strip():
            self.database.setDefect(reqId, "badtype", 0, url)
        return ct

    def conditional_fetch(self, ct, url, reqId):
        type_condition = self.getMaxPrefix(ct) in self.types
        prefix_condition = self.getMaxPrefixUri(url) in self.uris

        if not prefix_condition:
            self.database.setFinished(reqId)
            print("Uri not accepted: "+url)
        elif not type_condition:
            self.database.setFinished(reqId)
            print("Content-type not accepted: "+ct+" ("+url+")")
        else:
            self.fetch_response(url, reqId, ct)

    def fetch_response(self, url, reqId, ct):
        r = requests.get(url, allow_redirects=False)
        self.database.setResponse(reqId, r.url.encode('utf-8'), r.status_code, ct, r.text)

    def make_links_absolute(self, soup, url, tagL):
        for tag in soup.findAll(tagL, href=True):
            if 'href' in tag.attrs:
                tag['href'] = urljoin(url, tag['href'])

    def make_sources_absolute(self, soup, url, tagL):
        for tag in soup.findAll(tagL):
            tag['src'] = urljoin(url, tag['src'])

    def check_links(self, links, transactionId, tag):
        for link in links:
            url = link.get(tag)
            if url is not None:
                urlNoAnchor = url.split('#')[0]

                addr = urllib.quote(urlNoAnchor.encode('utf-8'))
                reqId = self.database.setLink(transactionId, addr, self.depth+1)
                self.database.setScriptParams(transactionId, addr, 'GET',
                                              parse_qs(urlparse(url).query, 
                                                       True)) 
 
                if self.really_get_link(reqId):
                    self.getLink(url, reqId, transactionId)

    def really_get_link(self, reqId):
        return (reqId != -1) and (self.maxDepth == 0 or self.depth < self.maxDepth)

    def getMaxPrefix(self, ctype):
        prefList = self.trie.prefixes(unicode(ctype, encoding="utf-8"))
        if len(prefList) > 0:
            return prefList[-1]
        else:
            return ctype

    def getMaxPrefixUri(self, uri):
        prefList = self.uriTrie.prefixes(uri)
        if len(prefList) > 0:
            return prefList[-1]
        else:
            return uri
