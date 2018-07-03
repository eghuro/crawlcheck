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
        fsize = transaction.cache['size']
        self.__red.hset("dupurl", transaction.file, transaction.uri)
        self.__duptest(fsize, transaction)
        return

    def __duptest(self, fsize, transaction):
        """Stage 1 of the duplication testing.
        If the file size was already seen, we look for possible duplicates.
        Otherwise just record the size.
        """

        if self.__red.hexists("dupsize", fsize):
            h = self.__hashfile(transaction)
            self.__red.hset("duphash", transaction.file, h)
            self.__compare(fsize, transaction, h)
            lst = set(json.loads(self.__red.hget("dupsize", fsize)))
            lst.add(transaction.file)
            self.__red.hset("dupsize", fsize, json.dumps(list(lst)))
        else:
            self.__red.hset("dupsize", fsize, json.dumps([transaction.file]))

    def __compare(self, fsize, transaction, reference_hash):
        """Stage 2 of the duplication testing.
        Compare the transaction for possible duplication candidates.

        Returns a list of files listed in the set, that were removed
        (possibly due to tmp limit)
        """

        for f in json.loads(self.__red.hget("dupsize", fsize)):
            if self.__are_different(f, transaction):
                if not self.__red.hexists("duphash", f):
                    self.__red.hset("duphash", f, self.__hashfile(transaction))
                if self.__red.hget("duphash", f) == reference_hash:
                    self.__journal.foundDefect(transaction.idno,
                                               "dup",
                                               "Duplicate pages",
                                               self.__red.hget("dupurl", f),
                                               0.7)

    def __are_different(self, file, transaction):
        return file != transaction.file and self.__red.hget("dupurl", file) != transaction.uri

    def __hashfile(self, tr, blocksize=65536):
        hasher = hashlib.sha512()
        hasher.update(tr.getContent())
        return hasher.hexdigest()
