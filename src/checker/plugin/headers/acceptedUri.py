from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import logging

class ExpectedUri(IPlugin):

    category = PluginType.HEADER
    id = "acceptedUri"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None
        self.__journal = None

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        self.__journal = journal

    def filter(self, transaction, r):
        if len(self.__conf.regex_acceptor.getAcceptingPlugins(transaction.uri)) == 0:
            self.__log.debug(transaction.uri + " is not accepted by any available plugin")
            raise FilterException()
