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

    def setDb(self, DB):
        self.database = DB

    def setTypes(self, types):
        self.types = types
        self.trie = marisa_trie.Trie(types)

    def check(self, transactionId, content):
        """ Najde tagy <a>, <link>, vybere atribut href, ulozi jako odkazy,
            stahne obsah jako dalsi transakci.
        """
        soup = BeautifulSoup(content, 'html.parser')
        uri = self.database.getUri(transactionId)
        
        self.make_links_absolute(soup, uri,'a')
        links = soup.find_all('a')
        self.check_links(links, "Link to ", transactionId, 'href')

        self.make_links_absolute(soup, uri, 'link')
        links2 = soup.find_all('link')
        self.check_links(links2, "Linked resource: ", transactionId, 'href')

        self.make_sources_absolute(soup, uri, 'img')
        images = soup.find_all('img')
        self.check_links(images, "Image: ", transactionId, 'src')

        return

    def getId(self):
        return "linksFinder"

    def getLink(self, url, reqId, srcId):
       try:
          print "Inspecting "+url
          r = requests.head(url)
          if r.status_code != 200:
             self.database.setDefect(srcId, "badlink", 0, url)
          if 'content-type' in r.headers.keys():
             ct = r.headers['content-type']
          else:
             ct = ''
          if self.getMaxPrefix(ct) in self.types:
            print "Downloading "+url
            r = requests.get(url)
            self.database.setResponse(reqId, r.status_code, ct, r.text.encode("utf-8").strip()[:65535])
          else: print "Content type not accepted: "+ct
       except InvalidSchema:
          print "Invalid schema"
       except ConnectionError:
          print "Connection error"
       except MissingSchema:
          print "Missing schema"

    def make_links_absolute(self, soup, url, tag):
        print "Make links absolute: "+url
        for tag in soup.findAll(tag, href=True):
           if 'href' in tag.attrs:
              tag['href'] = urlparse.urljoin(url, tag['href'])

    def make_sources_absolute(self, soup, url, tag):
        for tag in soup.findAll(tag):
            tag['src'] = urlparse.urljoin(url, tag['src'])

    def check_links(self, links, logMsg, transactionId, tag):
        for link in links:
            url = link.get(tag)
            if url is not None:
                urlNoAnchor = url.split('#')[0]

                reqId = self.database.setLink(transactionId, urllib.quote(urlNoAnchor.encode('utf-8')))
                print logMsg+str(url.decode('utf-8'))
                if reqId != -1:
                    self.getLink(url, reqId, transactionId)

    def getMaxPrefix(self, ctype):
        prefList = self.trie.prefixes(unicode(ctype, encoding="utf-8"))
        if len(prefList) > 0:
            return prefList[-1]
        else: return ctype
