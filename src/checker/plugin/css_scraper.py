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

    def push_db(self, transactionId, style, comment):
        uri = self.database.getUri(transactionId)
        reqId = self.database.setLink(transactionId, urllib.quote(uri.encode('utf-8')), 0)
        if reqId != -1:
            self.database.setResponse(reqId, urllib.quote(uri.encode('utf-8')), 200, 'text/css', style)
        else:
            print "Error inserting " + comment +" CSS for transaction "+transactionId

    def process_internal(self, transactionId, style):
        push_db(transactionId, style , "internal")

        # zkontroluje velikost vlozeneho CSS, pokud presahuje vybranou mez, oznacime jako chybu
        size = len(style.encode('utf-8'))
        LIMIT = 1024
        if size > LIMIT:
            self.database.setDefect(transactionId, 'seo:huge_internal', 0, size)
        return reqId

    def process_inline(self, transactionId, style):
        push_db(transactionId, style, "inline")
        # TODO: pokud zaznamenat existujici inliny do pole, pokud se tam jiz vyskytuje podretezec, 
        # oznacit duplikaci jako defekt

        # TODO: zkoumat id/classy, zda tam neni podretezec inline css
