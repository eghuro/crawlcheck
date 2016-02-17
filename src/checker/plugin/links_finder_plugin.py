from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
from requests.exceptions import InvalidSchema
from requests.exceptions import ConnectionError
from requests.exceptions import MissingSchema
import requests
import urlparse
import urllib
import marisa_trie

class LinksFinder(IPlugin):

    def __init__(self):
        self.database = None
        self.types = None
        self.trie = None
        self.uris = None
        self.uriTrie = None
        self.maxDepth = 0 #unlimited
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
          r = requests.head(url)
          if r.status_code >= 400:
             self.database.setDefect(srcId, "badlink", 0, url)
             self.database.setFinished(reqId)
             return
          if 'content-type' in r.headers.keys():
             ct = r.headers['content-type']
          elif 'Content-Type' in r.headers.keys():
             ct = r.headers['Content-Type']
          else:
             ct = ''
          if not ct.strip():
             self.database.setDefect(srcId, "badtype", 0, url)
          
          if self.getMaxPrefix(ct) in self.types:
             if self.getMaxPrefixUri(url) in self.uris:
                r = requests.get(url, allow_redirects=False)
                self.database.setResponse(reqId, r.url.encode('utf-8'), r.status_code, ct, r.text)
             else:
                print("Uri not accepted: "+url)
                self.database.setFinished(reqId)
          else: 
            print("Content type not accepted: "+ct+" ("+url+")")
            self.database.setFinished(reqId)
       except InvalidSchema:
          print("Invalid schema")
          self.database.setFinished(reqId)
       except ConnectionError:
          print("Connection error")
          self.database.setFinished(reqId)
       except MissingSchema:
          print("Missing schema")
          self.database.setFinished(reqId)

    def make_links_absolute(self, soup, url, tagL):
        for tag in soup.findAll(tagL, href=True):
           if 'href' in tag.attrs:
              tag['href'] = urlparse.urljoin(url, tag['href'])

    def make_sources_absolute(self, soup, url, tagL):
        for tag in soup.findAll(tagL):
            tag['src'] = urlparse.urljoin(url, tag['src'])

    def check_links(self, links, transactionId, tag):
        for link in links:
            url = link.get(tag)
            if url is not None:
                urlNoAnchor = url.split('#')[0]
                # urlNoQuery = urlNoAnchor.split('?')[0]

                reqId = self.database.setLink(transactionId, urllib.quote(urlNoAnchor.encode('utf-8')), self.depth+1)
                if reqId != -1:
                  if self.maxDepth == 0 or self.depth < self.maxDepth:
                    self.getLink(url, reqId, transactionId)

    def getMaxPrefix(self, ctype):
        prefList = self.trie.prefixes(unicode(ctype, encoding="utf-8"))
        if len(prefList) > 0:
            return prefList[-1]
        else: return ctype

    def getMaxPrefixUri(self, uri):
        prefList = self.uriTrie.prefixes(uri)
        if len(prefList) > 0:
            return prefList[-1]
        else: return uri
