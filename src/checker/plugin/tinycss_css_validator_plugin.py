from common import PluginType
import tinycss
from yapsy.IPlugin import IPlugin
import logging


class CssValidator(IPlugin):
    
    category = PluginType.CHECKER
    id = "tinycss"
    
    
    def __init__(self):
        self.journal = None

    def setJournal(self, journal):
        self.journal = journal

    def check(self, transaction):
        """Pusti validator, ulozi chyby.
        """
        try:
            parser = tinycss.make_parser('page3')
            data = str(transaction.getContent(), 'utf-8')
            stylesheet = parser.parse_stylesheet(data)
            for error in stylesheet.errors:
                self.journal.foundDefect(transaction.idno, "stylesheet", "Stylesheet error", [error.line, error.reason], 0.7)
        except UnicodeDecodeError as e:
            logging.getLogger().debug("Unicode decode error: "+format(e))
        return
