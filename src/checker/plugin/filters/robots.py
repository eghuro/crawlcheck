from filter import FilterException, Reschedule
from common import PluginType
from yapsy.IPlugin import IPlugin
import reppy
from reppy.robots import Robots
from reppy.cache import RobotsCache
from reppy.exceptions import ReppyException
from yapsy.IPlugin import IPlugin
import logging
import time

logging.getLogger("reppy").setLevel(logging.CRITICAL)

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
        self.__robots = RobotsCache(capacity=100,
                                    timeout=self.__conf.getProperty('timeout', 0))

    def setJournal(self, journal):
        pass

    def setQueue(self, queue):
        self.__queue = queue

    def filter(self, tran):

        try:
            # grab sitemaps
            maps = set(self.__robots.get(tran.uri).sitemaps)

            # link robots.txt from transaction, but mark transaction as visited
            robots_url = Robots.robots_url(tran.uri)

            diff_map = maps - self.__known_maps
            if len(diff_map) > 0:
                robots_transaction = self.__queue.push_virtual_link(robots_url,
                                                                    tran)
                for new_map in diff_map:
                    self.__log.debug("Discovered sitemap: "+new_map)
                    self.__queue.push_link(new_map, robots_transaction)
                self.__known_maps.update(maps)

            self.__log.debug("Testing robots.txt for " + tran.uri)
            agent = self.__conf.getProperty("agent")

            if not self.__robots.allowed(tran.uri, agent):
                self.__log.debug("Skipping " + tran.uri + " as robots.txt " +
                                 "prevent " + agent + " from fetching it")
                raise FilterException()
            else:
                delay = self.__robots.get(tran.uri).agent(agent).delay
                if delay is not None:
                    robots_url = Robots.robots_url(tran.uri)
                    if robots_url in self.__visit_times:
                        vt = self.__visit_times[robots_url]
                        self.__log.debug("Got timestamp for robots.txt file " +
                                         robots_url + ": " +
                                         str(vt) + ", current: " +
                                         str(time.time()) + " delay: " +
                                         str(delay))
                        sleep_time = delay - (time.time() - vt)
                        bound = self.__conf.getProperty("reschedule", 5)
                        if sleep_time > bound:
                            self.__log.warn("Should sleep for " +
                                            str(sleep_time) +
                                            " - rescheduling")
                            raise Reschedule()
                        elif sleep_time > 0:
                            self.__log.info("Sleep for " + str(sleep_time) +
                                            " due to crawl delay")
                            self.__log.debug("Robots.txt: " + robots_url)
                            time.sleep(sleep_time)
                    else:
                        self.__log.debug("New robots.txt with crawl delay: " +
                                         robots_url)
        except TypeError as e:
            self.__log.warning("Error while handling robots.txt for " +
                               tran.uri + ", not rejecting")
            self.__log.debug(str(e))
        except ValueError as e:
            self.__log.debug("Value error while parsing robots.txt for " +
                             tran.uri + ": " + str(e))
        except ReppyException as e:
            self.__log.debug("ReppyException: "+str(e))

    def getTimeSubscriber(self):
        return TimeSubscriber(self)

    def markVisit(self, url, t):
        robots_url = Robots.robots_url(url)
        self.__visit_times[robots_url] = t

# See Reppy references:
# http://pythonhackers.com/p/mt3/reppy
# https://github.com/seomoz/reppy
# http://pythonhackers.com/p/mt3/reppy


class TimeSubscriber(object):

    def __init__(self, rfilter):
        self.__plugin = rfilter

    def markStart(self, t, url):
        self.__plugin.markVisit(url, t)
