from common import PluginType
import tinycss
from yapsy.IPlugin import IPlugin
import logging


class CssValidator(IPlugin):

    category = PluginType.CHECKER
    id = "tinycss"
    contentTypes = ["text/css"]

    def __init__(self):
        self.__journal = None

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        """Pusti validator, ulozi chyby.
        """
        try:
            parser = tinycss.make_parser('page3')
            c = transaction.getContent()
            if type(c) == str:
                data = c
            else:
                data = str(transaction.getContent(), 'utf-8')
            stylesheet = parser.parse_stylesheet(data)
            for error in stylesheet.errors:
                self.__journal.foundDefect(transaction.idno, "stylesheet",
                                           "Stylesheet error",
                                           [error.line, error.reason], 0.7)
        except UnicodeDecodeError as e:
            logging.getLogger(__name__).debug("Unicode decode error: " +
                                              format(e))
        return
