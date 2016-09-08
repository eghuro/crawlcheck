from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin


class OpenGraph(IPlugin):

    category = PluginType.CRAWLER
    id = "openGraphCrawler"


    def __init__(self):
        self.__queue = None

        self.__properties = ['og:image', 'og:audio', 'og:video']

    def setJournal(self, journal):
        pass

    def setQueue(self, queue):
        self.__queue = queue

    def check(self, transaction):
        soup = BeautifulSoup(transaction.getContent(), 'html.parser')

        for meta in soup.find('head').find_all('meta'):
            if 'property' in meta.attrs:
                if meta.attrs['property'] in self.__properties:
                    self.__queue.push_link(meta.attrs['content'], transaction)
                elif OpenGraph.__is_url(meta.attrs['property'])
                    self.__queue.push_link(meta.attrs['content'], transaction)
                elif meta.attrs['property'] == 'og:url' and meta.attrs['content'] != transaction.uri:
                    self.__queue.push_link(meta.attrs['content'], transaction)

    @staticmethod
    def __is_url(self, text):
        return text.startswith('og:') and text.endswith(':url') and text != 'og.url'
