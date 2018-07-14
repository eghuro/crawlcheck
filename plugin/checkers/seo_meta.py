try:
    from crawlcheck.checker.common import PluginType, getSoup
except ImportError:
    from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin
import logging


class MetaTagValidator(IPlugin):

    category = PluginType.CHECKER
    id = "seometa"
    contentTypes = ["text/html"]

    __defects = {"seo:multidsc": "Multiple description meta tags found",
                 "seo:nodsc": "No description meta tag found",
                 "seo:multikeys": "Multiple keywords meta tags found",
                 "seo:nokeys": "No keywords meta tags found"}
    __severity = 0.4

    def __init__(self):
        self.__journal = None

    def setJournal(self, journal):
        self.__journal = journal

    def __classify(self, head, name, idno, zero, multi):
        foo = head.find_all('meta', {'name': name})
        if len(foo) > 1:
            clas = multi
            dsc = str(len(foo))
        elif len(foo) == 0:
            clas = zero
            dsc = ""
        else:
            return

        self.__journal.foundDefect(idno, clas,
                                   MetaTagValidator.__defects[clas],
                                   dsc, MetaTagValidator.__severity)

    def check(self, transaction):
        """Pusti validator, ulozi chyby.
        """
        for html in getSoup(transaction).find_all('html', limit=1):
            for head in html.find_all('head', limit=1):
                self.__classify(head, 'description', transaction.idno,
                                "seo:nodsc", "seo:multidsc")

                self.__classify(head, 'keywords', transaction.idno,
                                "seo:nokeys", "seo:multikeys")
        return
