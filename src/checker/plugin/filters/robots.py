from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import reppy
from reppy.cache import RobotsCache
from reppy.exceptions import ReppyException
from yapsy.IPlugin import IPlugin
import logging

class RobotsFilter(IPlugin):

    category = PluginType.FILTER
    id = "robots"

    def __init__(self):
        self.__log = logging.getLogger()
        self.__conf = None
        self.__robots = RobotsCache()

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        pass

    def filter(self, transaction):

        #TODO: crawl delay
        agent = self.__conf.getProperty("agent")
        self.__log.debug("Testing robots.txt for "+transaction.uri)
        try:
            if not self.__robots.allowed(transaction.uri,agent):
                self.__log.debug("Skipping "+transaction.uri+" as robots.txt prevent "+agent+" from fetching it")
                raise FilterException()
        except ReppyException as e:
            self.__log.debug("ReppyException: "+str(e))
