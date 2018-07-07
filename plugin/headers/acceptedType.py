
from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import logging


class AcceptedType(IPlugin):

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

    def setAcceptable(self, types, extended):
        self.__types = types
        self.__extended = extended
        self.__log.debug("Acceptable types: " + str(types))
        self.__log.debug("Plugins with extended acceptable type check: " + str([p.id for p in extended]))

    def filter(self, transaction, headers):
        self.__log.debug("Testing type acceptability for " + transaction.type)
        if transaction.type not in self.__types:
            for p in self.__extended:
                try:
                    if self.__conf.regex_acceptor.accept(transaction.uri, p.id) and p.acceptType(transaction.type):
                        self.__log.debug("Extended plugin " + p.id)
                        return
                except:
                    self.__log.warn(p.id + " should have acceptType method but hasn't")
            
            self.__log.debug(transaction.type + " is not accepted by any " +
                             "available plugin")
            raise FilterException()
