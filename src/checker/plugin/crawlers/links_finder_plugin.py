from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
from urllib.parse import urlparse, urljoin
import urllib.parse



class LinksFinder(IPlugin):

    category = PluginType.CRAWLER
    id = "linksFinder"
    
    
    def __init__(self):
        self.queue = None


    def setJournal(self, journal):
        pass


    def setQueue(self, queue):
        self.queue = queue


    def check(self, transaction):
        """ Najde tagy <a>, <link>, <img>, <iframe>, <frame>,
            vybere atribut href, resp. src, ulozi jako odkazy
        """

        soup = BeautifulSoup(transaction.getContent(), 'html.parser')

        self.updateCanonical(soup, transaction)

        self.checkType(soup, ['a', 'link'], 'href', transaction)
        self.checkType(soup, ['img', 'iframe', 'frame'], 'src', transaction)

        return

    def updateCanonical(self, soup, transaction):
       for html in soup.find_all('html', limit=1):
            for head in html.find_all('head', limit=1):
                for link in head.find_all('link'):
                    if ('rel' in link.attrs) and ('href' in link.attrs):
                        if link['rel'] == 'canonical':
                            transaction.changePrimaryUri(link['href'])
                            return

    def checkType(self, soup, tagL, attr, transaction):
        
        if attr == 'href':
            self.make_links_absolute(soup, transaction.uri, tagL)
        elif attr == 'src':
            self.make_sources_absolute(soup, transaction.uri, tagL)

        images = soup.find_all(tagL)

        self.check_links(images, transaction, attr)
        return

   
   
    def make_links_absolute(self, soup, url, tagL):
        
        for tag in soup.findAll(tagL, href=True):
            if 'href' in tag.attrs:
                tag['href'] = urljoin(url, tag['href'])


    def make_sources_absolute(self, soup, url, tagL):
        
        for tag in soup.findAll(tagL):
            if 'src' in tag.attrs:
                tag['src'] = urljoin(url, tag['src'])


    def check_links(self, links, transaction, tag):

        for link in links:
            url = link.get(tag)
            
            if url is not None:
                p = urlparse(url)
                if p.scheme not in ['http', 'https']:
                    continue #check only HTTP(S) - no FTP, MAILTO, etc.

                urlNoAnchor = url.split('#')[0]

                addr = urllib.parse.quote(urlNoAnchor.encode('utf-8'))
                #et = None
                #log.debug("Tag: "+tag+"; looking for img here")
                #if tag == "img":
                #    et = "image/"
                self.queue.push_link(addr, transaction) #duplicates handled in queue
