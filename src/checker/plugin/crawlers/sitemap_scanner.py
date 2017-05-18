from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
from urllib.parse import urlparse
import logging


class SitemapScanner(IPlugin):

    category = PluginType.CRAWLER
    id = "sitemapScanner"

    def __init__(self):
        self.queue = None

    def setJournal(self, journal):
        pass

    def setQueue(self, queue):
        self.queue = queue

    def check(self, transaction):
        soup = BeautifulSoup(transaction.getContent(), 'lxml-xml')
        urls = soup.findAll('url')
        log = logging.getLogger(__name__)
        if not urls:
            return
        for u in urls:
            loc = u.find('loc').string
            p = urlparse(loc)
            if p.scheme not in ['http', 'https']:
                continue
            log.debug("Link from sitemap ("+transaction.uri+") to "+loc)
            self.queue.push_link(loc, transaction)

# See: https://gist.github.com/chrisguitarguy/1305010
