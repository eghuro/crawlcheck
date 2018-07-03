from common import PluginType
from yapsy.IPlugin import IPlugin
import logging
import hashlib


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
        self.__size_dups = dict()
        self.__hash = dict()
        self.__urls = dict()
        self.__log = logging.getLogger(__name__)

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        """Check if the content matches any page we've already seen."""

        fsize = transaction.cache['size']
        self.__urls[transaction.file] = transaction.uri
        self.__duptest(fsize, transaction)
        return

    def __duptest(self, fsize, transaction):
        """Stage 1 of the duplication testing.
        If the file size was already seen, we look for possible duplicates.
        Otherwise just record the size.
        """

        if fsize in self.__size_dups:
            h = self.__hashfile(transaction.file)
            self.__hash[transaction.file] = h
            self.__compare(fsize, transaction, h)
            self.__size_dups[fsize].add(transaction.file)
        else:
            self.__size_dups[fsize] = set([transaction.file])

    def __compare(self, fsize, transaction, reference_hash):
        """Stage 2 of the duplication testing.
        Compare the transaction for possible duplication candidates.

        Returns a list of files listed in the set, that were removed
        (possibly due to tmp limit)
        """

        for f in self.__size_dups[fsize]:
            if self.__are_different(f, transaction):
                if f not in self.__hash:
                    self.__hash[f] = self.__hashfile(transaction.file)
                if self.__hash[f] == reference_hash:
                    #if self.__file_cmp(f, transaction):
                    self.__journal.foundDefect(transaction.idno,
                                               "dup",
                                               "Duplicate pages",
                                               self.__urls[f], 0.7)

    def __are_different(self, f, transaction):
        return f != transaction.file and self.__urls[f] != transaction.uri

    def __hashfile(self, path, blocksize=65536):
        with open(path, 'rb') as afile:
            hasher = hashlib.sha512()
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)
            return hasher.hexdigest()
