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
        self.__log = logging.getLogger(__name__)
        self.__conf = None
        self.__robots = None

    def setConf(self, conf):
        self.__conf = conf
        self.__robots = RobotsCache(timeout=self.__conf.getProperty('timeout'))

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
        except TypeError as e:
            self.__log.warning("Error while handling robots.txt for "+transaction.uri)
            self.__log.debug(str(e))
        except ReppyException as e:
            self.__log.debug("ReppyException: "+str(e))
