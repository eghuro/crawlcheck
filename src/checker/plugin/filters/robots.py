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
        self.__queue = None
        self.__known_maps = set()

    def setConf(self, conf):
        self.__conf = conf
        self.__robots = RobotsCache(timeout=self.__conf.getProperty('timeout'), capacity=100)

    def setJournal(self, journal):
        pass

    def setQueue(self, queue):
        self.__queue = queue

    def filter(self, transaction):

        #grab sitemaps
        maps = self.__robots.sitemaps #(transaction.uri)
        for new_map in self.__known_maps - set(maps):
            self.__log.debug("Discovered sitemap: "+new_map)
            self.__queue.push_link(new_map, None)
            #TODO: maybe better get robots.txt URI, put it into DB and link sitemaps from there
            #anyway there are loose nodes in the tree ... but we are then able to discover orphaned pages
        self.__known_maps.update(maps)

        #crawl delay?
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

#Reppy references:
#http://pythonhackers.com/p/mt3/reppy
#https://github.com/seomoz/reppy
#http://pythonhackers.com/p/mt3/reppy

