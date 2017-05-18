from common import PluginType
from yapsy.IPlugin import IPlugin
import logging
import tempfile
import re


class SitemapGenerator(IPlugin):

    category = PluginType.POSTPROCESS
    id = "sitemap_generator"

    header = ('<?xml version="1.0" encoding="utf-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
              '   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
              '   xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap'
              '/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd'
              '">\n')

    line = "\t<url>\n\t\t<loc>%s</loc>\n\t</url>\n"

    def __init__(self):
        self.__log = logging.getLogger(__name__)

    def setConf(self, conf):
        self.__conf = conf

    def setDb(self, db):
        self.__db = db

    def setJournal(self, journal):
        pass

    def process(self):
        outfile = self.__conf.getProperty('sitemap-file')
        regex = self.__conf.getProperty('sitemap-regex')
        if regex is None:
            self.__log.error("No regex for sitemap")
            return

        r = re.compile(regex)
        if outfile is not None:
            self.__log.info("Generating sitemap into " + outfile)
            with open(outfile, 'w') as out:
                self.__write_file(out, r)
        else:
            self.__log.warn("sitemap-file property not found in config")
            pref = self.__conf.getProperty("tmpPrefix")
            suf = "-sitemap.xml"
            with tempfile.NamedTemporaryFile(delete=False, prefix=pref,
                                             suffix=suf, mode='w') as out:
                self.__write_file(out, r)
                outfile = out.name
        self.__log.info("Sitemap written into %s" % outfile)

    def __write_file(self, out, r):
        out.write(SitemapGenerator.header)
        self.__write_urls(out, r)
        out.write('</urlset>')

    def __write_urls(self, out, r):
        for url in self.__db.get_urls():
            if r.match(url):
                out.write(SitemapGenerator.line % url)
