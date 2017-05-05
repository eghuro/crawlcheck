from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import reppy
from reppy.robots import Robots
from reppy.cache import RobotsCache
from reppy.exceptions import ReppyException
from yapsy.IPlugin import IPlugin
import logging
import time

class RobotsFilter(IPlugin):

    category = PluginType.FILTER
    id = "robots"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None
        self.__robots = None
        self.__queue = None
        self.__known_maps = set()
        self.__visit_times = dict()

    def setConf(self, conf):
        self.__conf = conf
        self.__robots = RobotsCache(timeout=self.__conf.getProperty('timeout'), capacity=100)

    def setJournal(self, journal):
        pass

    def setQueue(self, queue):
        self.__queue = queue

    def filter(self, transaction):

        #grab sitemaps
        maps = self.__robots.get(transaction.uri).sitemaps

        #link robots.txt from transaction, but mark transaction as visited
        robots_url = Robots.robots_url(transaction.uri)
        robots_transaction = self.__queue.push_virtual_link(robots_url, transaction)

        for new_map in self.__known_maps - set(maps):
            self.__log.debug("Discovered sitemap: "+new_map)
            self.__queue.push_link(new_map, robots_transaction)
        self.__known_maps.update(maps)

        self.__log.debug("Testing robots.txt for " + transaction.uri)
        agent = self.__conf.getProperty("agent")
        try:
            if not self.__robots.allowed(transaction.uri, agent):
                self.__log.debug("Skipping " + transaction.uri + " as robots.txt prevent " +
                                 agent + " from fetching it")
                raise FilterException()
            else:
                delay = self.__robots.get(transaction.uri).agent(agent).delay
                if delay is not None:
                    robots_url = Robots.robots_url(transaction.uri)
                    if robots_url in self.__visit_times:
                        sleep_time = time.time() - self.__visit_times[robots_url] - delay
                        if sleep_time > 0:
                            self.__log.info("Sleep for " + sleep_time + " due to crawl delay")
                            time.sleep(sleep_time)
                    self.__visit_times[robots_url] = time.time()
        except TypeError as e:
            self.__log.warning("Error while handling robots.txt for "+transaction.uri)
            self.__log.debug(str(e))
        except ReppyException as e:
            self.__log.debug("ReppyException: "+str(e))

#Reppy references:
#http://pythonhackers.com/p/mt3/reppy
#https://github.com/seomoz/reppy
#http://pythonhackers.com/p/mt3/reppy

