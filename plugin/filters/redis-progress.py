try:
    from crawlcheck.checker.filter import FilterException
    from crawlcheck.checker.common import PluginType
except ImportError:
    from filter import FilterException
    from common import PluginType
from yapsy.IPlugin import IPlugin
import logging
import redis
from timeit import default_timer as timer


class RedisProgress(IPlugin):

    category = PluginType.FILTER
    id = "redis-progress"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None
        self.__redis = None

    def setConf(self, conf):
        self.__conf = conf
        self.__redis = redis.StrictRedis(host=conf.getProperty('redisHost'),
                                         port=conf.getProperty('redisPort'),
                                         db=conf.getProperty('redisDb'))

    def setJournal(self, journal):
        pass

    def filter(self, transaction):
        self.__log.debug("Logging a visit")
        streamKey = "log" + self.__conf.getProperty('runIdentifier')
        start = timer()
        self.__run(streamKey, transaction)
        end = timer()
        self.__log.debug("Pushed log entry, execution lasted: " + str(end - start))

    def __run(self, streamKey, transaction):
        with self.__redis.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(streamKey)
                    pipe.lpush(streamKey, str(transaction.uri))
                    #pipe.multi()
                    #pipe.ltrim(streamKey, 0, 999) #max 1000 log records
                    pipe.expire(streamKey, 30*60) #30 mins for log, unless there are other changes
                    pipe.execute()
                    return
                except redis.WatchError:
                    continue

