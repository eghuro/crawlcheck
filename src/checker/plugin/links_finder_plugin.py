from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
from urlparse import urlparse, parse_qs, urljoin
import urllib
import marisa_trie
from net import Network



class LinksFinder(IPlugin):

    type = PluginType.CRAWLER
    
    
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
       self.database.setFinished(reqId)
   
   
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
