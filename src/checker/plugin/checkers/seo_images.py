from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
import logging


class ImageTagValidator(IPlugin):
    
    category = PluginType.CHECKER
    id = "seoimg"
    
    
    def __init__(self):
        self.__journal = None

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        """Pusti validator, ulozi chyby.
        """

        if 'soup' in transaction.cache and transaction.cache['soup']:
            soup = transaction.cache['soup']
        else:
            soup = BeautifulSoup(transaction.getContent(), 'lxml')
            transaction.cache['soup'] = soup

        for img in soup.find_all('img'):
            if 'src' in img.attrs:
                desc = img['src']
            else:
                desc = ""
            if 'width' not in img:
                self.__journal.foundDefect(transaction.idno,
                                           "seo:img:nowidth",
                                           "IMG tag with no width attribute",
                                           desc, 0.6)
            if 'height' not in img:
                self.__journal.foundDefect(transaction.idno,
                                           "seo:img:noheight",
                                           "IMG tag with no height attribute",
                                           desc, 0.6)
            #TODO: only jpg, png, gifs are allowed
            #TODO: check IMG dimensions match declared ones
        return
