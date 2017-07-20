from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin


class CssScraper(IPlugin):

    category = PluginType.CHECKER
    id = "css_scraper"

    def __init__(self):
        self.journal = None

    def setJournal(self, journal):
        self.journal = journal

    def check(self, transaction):
        soup = getSoup(transaction)
        self.internal(soup, transaction)
        self.inlines(soup, transaction)

    def internal(self, soup, transaction):
        data = self.scan_internal(soup)
        if data is not None:
            self.process_internal(transaction, data)

    def inlines(self, soup, transaction):
        data = self.scan_inline(soup)
        self.inlines_seen = set()
        for inline in data:
            self.process_inline(transaction, inline)

    def scan_internal(self, soup):
        style = soup.find('style')
        if style is not None:
            return style.string
        else:
            return None

    def scan_inline(self, soup):
        inlines = []
        for child in soup.descendants:
            try:
                if 'style' in child.attrs:
                    inlines.append(child['style'])
            except AttributeError:
                pass
        return inlines

    def process_internal(self, transaction, style):
        # zkontroluje velikost vlozeneho CSS, pokud presahuje vybranou mez,
        # oznacime jako chybu
        size = len(style.encode('utf-8'))
        LIMIT = 1024
        if size > LIMIT:
            self.journal.foundDefect(transaction.idno, 'seo:huge_internal',
                                     "Internal CSS bigger than 1024", size,
                                     0.5)

    def process_inline(self, transaction, style):
        if style in self.inlines_seen:
            self.duplicit_inline(transaction, style)
        else:
            self.inlines_seen.add(style)

    def duplicit_inline(self, transaction, style):
        self.journal.foundDefect(transaction.idno, 'seo:duplicit_inline',
                                 "Duplicate inline CSS", style, 0.1)
