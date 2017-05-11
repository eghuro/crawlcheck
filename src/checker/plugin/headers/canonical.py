from filter import FilterException
from common import PluginType
from yapsy.IPlugin import IPlugin
import logging


class CanonicalFilter(IPlugin):

    category = PluginType.HEADER
    id = "canonical"

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__conf = None

    def setConf(self, conf):
        self.__conf = conf

    def setJournal(self, journal):
        pass

    def filter(self, transaction, headers):
        if 'Link' in headers:
            parts = headers['Link'].split(';')
            if parts[1].strip() == 'rel="canonical"':
                canonical = parts[0][1:-1] #Link: <http://example.com/page.html>; rel="canonical"
                transaction.changePrimaryUri(canonical)
