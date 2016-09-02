from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import logging

class DepthFilter(IPlugin):

    category = PluginType.FILTER
    id = "depth"

    def __init__(self):
        self.__log = logging.getLogger()
        self.__conf = None

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        pass

    def filter(self, transaction):
        maxDepth = self.__conf.getProperty("maxDepth")
        if transaction.depth > maxDepth:
            self.__log.debug("Skipping "+transaction.uri+" as it's depth "+transaction.depth+" and max depth condition is "+maxDepth)
            raise FilterException()
