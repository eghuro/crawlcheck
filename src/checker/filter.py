import logging
import urllib.robotparser
import reppy
from reppy.cache import RobotsCache
from reppy.exceptions import ReppyException
from urllib.parse import urlparse
from http.client import RemoteDisconnected

class FilterException(Exception):

    pass


class DepthFilter:

    def __init__(self, conf):
        self.log = logging.getLogger()
        self.conf = conf

    def filter(self, transaction):
        if transaction.depth > self.conf.max_depth:
            self.log.debug("Skipping "+transaction.uri+" as it's depth "+transaction.depth+" and max depth condition is "+self.conf.max_depth)
            raise FilterException()

class RobotsFilter:

    def __init__(self, conf):
        self.__log = logging.getLogger()
        self.__conf = conf
        self.__robots = RobotsCache()

    def filter(self, transaction):

        #TODO: crawl delay
        self.__log.debug("Testing robots.txt for "+transaction.uri)
        try:
            if not self.__robots.allowed(transaction.uri, self.__conf.user_agent):
                self.__log.debug("Skipping "+transaction.uri+" as robots.txt prevent "+self.__conf.user_agent+" from fetching it")
                raise FilterException()
        except ReppyException as e:
            self.__log.debug("ReppyException: "+str(e))
