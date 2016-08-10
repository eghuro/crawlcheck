from common import PluginType
import tinycss
from yapsy.IPlugin import IPlugin


class CssValidator(IPlugin):
    
    type = PluginType.CHECKER
    
    
    def __init__(self):
        self.journal = None

    def setJournal(self, journal):
        self.journal = journal

    def getId(self):
        return "tinycss"

    def check(self, transaction):
        """Pusti validator, ulozi chyby.
        """
        try:
            parser = tinycss.make_parser('page3')
            stylesheet = parser.parse_stylesheet(transaction.getContent())
            for error in stylesheet.errors:
                self.journal.foundDefect(transaction, ["stylesheet", error.line, error.reason])
        except UnicodeDecodeError:
            print("Error")
        return
