from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
import logging


class MetaTagValidator(IPlugin):
    
    category = PluginType.CHECKER
    id = "seometa"
    
    
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

        for html in soup.find_all('html', limit=1):
            for head in html.find_all('head', limit=1):
                desc = head.find_all('meta', {'name' : 'description'})
                if len(desc) > 1:
                    self.__journal.foundDefect(transaction.idno,
                                               "seo:multidsc",
                                               "Multiple description meta tags found",
                                               str(len(desc)), 0.8)
                elif len(desc) == 0:
                    self.__journal.foundDefect(transaction.idno,
                                               "seo:nodsc",
                                               "No description meta tag found",
                                               "", 0.8)

                tags = head.find_all('meta', {'name' : 'keywords'})
                if len(tags) > 1:
                    self.__journal.foundDefect(transaction.idno,
                                               "seo:multikeys",
                                               "Multiple keywords meta tags found",
                                               str(len(tags)), 0.8)
                elif len(desc) == 0:
                    self.__journal.foundDefect(transaction.idno,
                                               "seo:nokeys",
                                               "No keywords meta tag found",
                                               "", 0.8)
        return
