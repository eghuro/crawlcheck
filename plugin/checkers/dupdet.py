try:
    from crawlcheck.checker.common import PluginType
except ImportError:
    from common import PluginType
from yapsy.IPlugin import IPlugin
import logging
import hashlib
import redis
import json


class DuplicateDetector(IPlugin):
    """Duplicate detector plugin.
    Look for possible duplicates in the pages that pass through.

    We compare just SHA512 hashes.

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
                                           db=transaction.conf.getProperty('redisDb', 0),
                                           charset="utf-8", decode_responses=True)
        h = self.__hashfile(transaction)
        duphash = "duphash" + transaction.conf.getProperty("runIdentifier")
        dupname = "dupname" + transaction.conf.getProperty("runIdentifier")

        if self.__red.pfadd(duphash, h) == 0: #exists
            p = self.__red.hget(dupname, h)
            if p != None:
                if str(p) in transaction.aliases:
                    self.__log.error("Same URI visited twice: " + p + " & " +transaction.uri)
                    return
                # duplicity
                self.__journal.foundDefect(transaction.idno,
                                           "dup",
                                           "Duplicit pages",
                                           str(p), 0.7)
            else:
                self.__log.warn("Hash was in hyperloglog but no name mapping. URL: " + transaction.uri)
                self.__red.hset(dupname, h, transaction.uri)
        else:
            self.__red.hset(dupname, h, transaction.uri)
        return

    def __hashfile(self, tr, blocksize=65536):
        hasher = hashlib.sha512()
        hasher.update(tr.getContent())
        return hasher.hexdigest()
