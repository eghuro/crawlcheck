from enum import Enum
from bs4 import BeautifulSoup


class PluginType(Enum):
    CRAWLER = 0
    CHECKER = 1
    FILTER = 2
    HEADER = 3
    POSTPROCESS = 4


class PluginTypeError(Exception):
    def __str__(self):
        return "Unknown plugin type"


def getSoup(transaction):
    if 'soup' in transaction.cache and transaction.cache['soup']:
        soup = transaction.cache['soup']
    else:
        soup = BeautifulSoup(transaction.getContent(), 'lxml')
        transaction.cache['soup'] = soup
    return soup

class ConfigurationError(Exception):
    def __init__(self, msg):
        self.msg = msg
