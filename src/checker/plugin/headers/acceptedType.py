from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import logging


class ExpectedType(IPlugin):

    category = PluginType.HEADER
    id = "acceptedType"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None
        self.__journal = None

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        self.__journal = journal

    def filter(self, transaction, headers):
        if transaction.type not in self.__conf.type_acceptor.uris:
            self.__log.debug(transaction.type + " is not accepted by any " +
                             "available plugin")
            raise FilterException()
