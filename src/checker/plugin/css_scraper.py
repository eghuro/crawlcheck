from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin

class CssScraper(IPlugin):
    def __init__(self):
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def getId(self):
        return "css_scraper"

    def check(self, transactionId, content):
        soup = BeautifulSoup(content, 'html.parser')
        self.internal(soup, transactionId)
        self.inlines(soup, transactionId)

    def internal(self, soup, transactionId):
        data = self.scan_internal(soup)
        if data is not None:
            self.process_internal(transactionId, data)

    def inlines(self, soup, transactionId):
        data = self.scan_inline(transactionId, soup)
        for inline in data:
            self.process_inline(transactionId, inline)

    def scan_internal(self, soup):
        style = soup.find('style')
        if style is not None:
            return style
        else
            return None

    def scan_inline(self, soup):
        inlines = []
        for child in soup.descendants:
            if style in child.attrs:
                inlines.append(child['style'])
        return inlines

    def process_internal(self, transactionId, style):
        pass

    def process_inline(self, transactionId, style):
        pass
