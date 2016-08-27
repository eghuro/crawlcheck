from yapsy.IPlugin import IPlugin
from tidylib import tidy_document
from common import PluginType


class Tidy_HTML_Validator(IPlugin):
    
    category = PluginType.CHECKER
    id = "tidyHtmlValidator"

    def __init__(self):
        self.journal = None

    def setJournal(self, journal):
        self.journal = journal

    def check(self, transaction):
        res = tidy_document(transaction.getContent(), keep_doc=True)
        print res[1]
