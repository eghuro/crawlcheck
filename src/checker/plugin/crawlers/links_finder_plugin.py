from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin
from urllib.parse import urlparse, urljoin
import urllib.parse



class LinksFinder(IPlugin):

    category = PluginType.CRAWLER
    id = "linksFinder"
    
    
    def __init__(self):
        self.__queue = None
        self.__tags = {'a' : 'href',
                       'link' : 'href',
                       'img' : 'src',
                       'iframe' : 'src',
                       'frame' : 'src'}


    def setJournal(self, journal):
        pass


    def setQueue(self, queue):
        self.__queue = queue


    def check(self, transaction):
        """ Najde tagy <a>, <link>, <img>, <iframe>, <frame>,
            vybere atribut href, resp. src, ulozi jako odkazy
        """

        soup = getSoup(transaction)
        self.updateCanonical(soup, transaction)

        self.check_links(soup.find_all(self.__tags.keys()), transaction,
                         self.__tags)

        return


    def updateCanonical(self, soup, transaction):
       for html in soup.find_all('html', limit=1):
            for head in html.find_all('head', limit=1):
                for link in head.find_all('link'):
                    if ('rel' in link.attrs) and ('href' in link.attrs):
                        if link['rel'] == 'canonical':
                            transaction.changePrimaryUri(link['href'])
                            return


    def check_links(self, links, transaction, tags):

        for link in links:
            url = link.get(tags[link.name])
            
            if url is not None:
                url = urljoin(transaction.uri, url)
                p = urlparse(url)
                if p.scheme not in ['http', 'https']:
                    continue #check only HTTP(S) - no FTP, MAILTO, etc.

                urlNoAnchor = url.split('#')[0]

                addr = urllib.parse.quote(urlNoAnchor.encode('utf-8'))

                et = None
                if link.name == "img":
                    et = "image/"
                self.__queue.push_link(addr, transaction) #dups handled there
