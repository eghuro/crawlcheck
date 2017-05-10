from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
from url_normalize import url_normalize
import logging

class Normalizer(IPlugin):

    category = PluginType.FILTER
    id = "normalize"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        pass

    def filter(self, transaction):
        normalized = url_normalize(transaction.uri)
        if transaction.uri != normalized:
            self.__log.debug("Normalizing: " + transaction.uri + " -> " + normalized)
            transaction.changePrimaryUri(url_normalize(transaction.uri))
