from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
from urllib.parse import urlparse
import logging
import gzip


class SitemapScanner(IPlugin):

    category = PluginType.CRAWLER
    id = "sitemapScanner"

    # https://www.sitemaps.org/protocol.html
    __limit_size = 50000000 # 50 MB
    __limit_records = 50000

    def __init__(self):
        self.__queue = None
        self.__journal = None

    def setJournal(self, journal):
        self.__journal = journal

    def setQueue(self, queue):
        self.__queue = queue

    def check(self, transaction):
        log = logging.getLogger(__name__)

        if transaction.type == 'application/gzip':
            with gzip.open(transaction.file, 'rb') as f:
                content = f.read()
                size = len(content)
        else:
            content = transaction.getContent()
            size = transaction.cache['size']

        soup = BeautifulSoup(content, 'lxml-xml')
        urls = soup.findAll('url')

        if not urls:
            return #no urls or not a sitemap.xml

        if len(soup.findAll('sitemap')) == 0 or \
           len(soup.findAll('sitemapindex')) == 0:
            return # not a sitemap.xml nor Sitemap index

        self.__test_conditions(size, len(urls), transaction.idno)
        self.__scan_urls(urls, transaction)


    def __scan_urls(self, urls, transaction):
        for u in urls:
            loc = u.find('loc').string
            p = urlparse(loc)
            if p.scheme not in ['http', 'https']:
                continue
            log.debug("Link from sitemap ("+transaction.uri+") to "+loc)
            self.__queue.push_link(loc, transaction)


    def __test_conditions(self, size, url_cnt, idno):
        if size > SitemapScanner__limit_size:
            self.__journal.foundDefect(idno, "sitemapsize",
                                       "Sitemap.xml size exceeds 50MiB",
                                       str(size), 0.6)

        if url_cnt > SitemapScanner.__limit_records:
            self.__journal.foundDefect(idno, "sitemaprecords",
                                       "Sitemap.xml exceeds 50 000 URLs",
                                       str(url_cnt), 0.6)


# See: https://gist.github.com/chrisguitarguy/1305010
