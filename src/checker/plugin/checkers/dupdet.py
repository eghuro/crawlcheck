from common import PluginType
from yapsy.IPlugin import IPlugin
import logging
import hashlib
import redis
import json


class DuplicateDetector(IPlugin):
    """Duplicate detector plugin.
    Look for possible duplicates in the pages that pass through.

    We compare file size, then hashes and then compare files themselves.

    Limitation: Detection is done partially by comparing individual downloaded
    files. If the limit on temp files is reached and some files are removed we
    might miss some duplicates.
    """

    # See: http://pythoncentral.io/finding-duplicate-files-with-python/
    # https://github.com/IanLee1521/utilities/blob/master/utilities/find_duplicates.py

    category = PluginType.CHECKER
    id = "dupdetect"

    @staticmethod
    def acceptType(ctype):
        return True

    def __init__(self):
        self.__journal = None
        self.__log = logging.getLogger(__name__)
        self.__red = None

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        """Check if the content matches any page we've already seen."""

        if self.__red is None:
            self.__red = redis.StrictRedis(host=transaction.conf.getProperty('redisHost', 'localhost'),
                                           port=transaction.conf.getProperty('redisPort', 6379),
                                           db=transaction.conf.getProperty('redisDb', 0))
        h = self.__hashfile(transaction)
        if self.__red.pfadd("duphash", h) == 1:
            # duplicate
            self.__journal.foundDefect(transaction.idno,
                                       "dup",
                                       "Duplicate pages",
                                       self.__red.hget("dupname", h),
                                       0.7)
        else:
            self.__red.hset("dupname", h, transaction.uri)
        return

    def __hashfile(self, tr, blocksize=65536):
        hasher = hashlib.sha512()
        hasher.update(tr.getContent())
        return hasher.hexdigest()
