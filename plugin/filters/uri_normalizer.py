try:
    from crawlcheck.checker.filter import FilterException
    from crawlcheck.checker.common import PluginType
except ImportError:
    from filter import FilterException
    from common import PluginType
from yapsy.IPlugin import IPlugin
from url_normalize import url_normalize
import logging


class Normalizer(IPlugin):

    category = PluginType.FILTER
    id = "uri_normalizer"

    def __init__(self):
        self.__log = logging.getLogger(__name__)

    def setConf(self, conf):
        pass

    def setJournal(self, journal):
        pass

    def filter(self, transaction):
        normalized = url_normalize(transaction.uri)
        if transaction.uri != normalized:
            self.__log.debug("Normalizing: " + transaction.uri + " -> " +
                             normalized)
            transaction.changePrimaryUri(url_normalize(transaction.uri))
