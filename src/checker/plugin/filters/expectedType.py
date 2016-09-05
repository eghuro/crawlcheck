from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import logging

class ExpectedType(IPlugin):

    category = PluginType.FILTER
    id = "expectedType"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None
        self.__journal = None

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        self.__journal = journal

    def filter(self, transaction):
        if transaction.expected is None:
            return
        if not transaction.type.startswith(transaction.expected):
            self.__log.debug("Got content type: "+transaction.type+", expected content type starting with "+transaction.expected + "(Could be CSRF with fake img?)")
            self.__journal.foundDefect(transaction.idno, "mistyped", "Content-type not expected", transaction.expected, 0.8)
