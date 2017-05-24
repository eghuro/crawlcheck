from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import logging


class ContentLengthFilter(IPlugin):

    category = PluginType.HEADER
    id = "contentLength"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        pass

    def filter(self, transaction, headers):
        if 'Content-Length' in headers:
            try:
                conlen = int(headers['Content-Length'])
                maxContent = self.__conf.getProperty("maxContentLength")
                if maxContent is not None:
                    if conlen > maxContent:
                        self.__log.warning("Content length too large for " +
                                           transaction.uri + " (got: " +
                                           str(conlen) + ", limit: " +
                                           str(maxContent)+") Skipping download.")
                        raise FilterException()
            except ValueError as e:
                self.__log.exception("Error reading headers, skipping download.", e)
                raise FilterException() from e
