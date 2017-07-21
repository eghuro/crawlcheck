from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin


class CssScraper(IPlugin):

    category = PluginType.CHECKER
    id = "css_scraper"

    def __init__(self):
        self.__journal = None

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        soup = getSoup(transaction)
        self.__internal(soup, transaction)
        self.__inlines(soup, transaction)

    def __internal(self, soup, transaction):
        data = self.__scan_internal(soup)
        if data is not None:
            self.__process_internal(transaction, data)

    def __inlines(self, soup, transaction):
        data = self.__scan_inline(soup)
        self.__inlines_seen = set()
        for inline in data:
            self.__process_inline(transaction, inline)

    def __scan_internal(self, soup):
        style = soup.find('style')
        if style is not None:
            return style.string
        else:
            return None

    def __scan_inline(self, soup):
        inlines = []
        for child in soup.descendants:
            try:
                if 'style' in child.attrs:
                    inlines.append(child['style'])
            except AttributeError:
                pass
        return inlines

    def __process_internal(self, transaction, style):
        # zkontroluje velikost vlozeneho CSS, pokud presahuje vybranou mez,
        # oznacime jako chybu
        size = len(style.encode('utf-8'))
        LIMIT = 1024
        if size > LIMIT:
            self.__journal.foundDefect(transaction.idno, 'seo:huge_internal',
                                       "Internal CSS bigger than 1024", size,
                                       0.5)

    def __process_inline(self, transaction, style):
        if style in self.__inlines_seen:
            self.__duplicit_inline(transaction, style)
        else:
            self.__inlines_seen.add(style)

    def __duplicit_inline(self, transaction, style):
        self.__journal.foundDefect(transaction.idno, 'seo:duplicit_inline',
                                   "Duplicate inline CSS", style, 0.1)
