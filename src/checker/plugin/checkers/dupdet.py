from common import PluginType
from yapsy.IPlugin import IPlugin
import logging
import hashlib
import filecmp
import os


class DuplicateDetector(IPlugin):
    # See: http://pythoncentral.io/finding-duplicate-files-with-python/
    # https://github.com/IanLee1521/utilities/blob/master/utilities/find_duplicates.py

    category = PluginType.CHECKER
    id = "dupdetect"

    def __init__(self):
        self.__journal = None
        self.__size_dups = dict()
        self.__hash = dict()
        self.__urls = dict()
        self.__log = logging.getLogger(__name__)

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        fsize = transaction.cache['size']
        self.__urls[transaction.file] = transaction.uri
        if fsize in self.__size_dups:
            h = self.__hashfile(transaction.file)
            self.__hash[transaction.file] = h
            for f in self.__size_dups[fsize]:
                if f != transaction.file and self.__urls[f] != transaction.uri:
                    if f not in self.__hash:
                        self.__hash[f] = self.__hashfile(transaction.file)
                    if self.__hash[f] == h:
                        if filecmp.cmp(f, transaction.file):
                            # duplicate (same size, same hash, same content)
                            self.__journal.foundDefect(transaction.idno, "dup",
                                                       "Duplicate pages",
                                                       self.__urls[f], 0.7)
            self.__size_dups[fsize].add(transaction.file)
        else:
            self.__size_dups[fsize] = set([transaction.file])
        return

    def __hashfile(self, path, blocksize=65536):
        with open(path, 'rb') as afile:
            hasher = hashlib.md5()
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)
            return hasher.hexdigest()
