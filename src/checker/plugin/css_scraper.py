from common import PluginType
from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin


class CssScraper(IPlugin):
    
    type = PluginType.CHECKER
    id = "css_scraper"
    
    
    def __init__(self):
        self.journal = None


    def setJournal(self, journal):
        self.journal = journal


    def check(self, transaction):
        soup = BeautifulSoup(transaction.getContent(), 'html.parser')
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


    #def push_db(self, transactionId, style, comment):
        #uri = self.database.getUri(transactionId)
        #reqId = self.database.setLink(transactionId, urllib.quote(uri.encode('utf-8')), 0)
        #if reqId != -1:
        #self.database.setResponse(reqId, urllib.quote(uri.encode('utf-8')), 200, 'text/css', style)
        #else:
        #    print("Error inserting " + comment +" CSS for transaction "+str(transactionId))


    def process_internal(self, transaction, style):
        #self.push_db(transactionId, style , "internal")

        # zkontroluje velikost vlozeneho CSS, pokud presahuje vybranou mez, oznacime jako chybu
        size = len(style.encode('utf-8'))
        LIMIT = 1024
        if size > LIMIT:
            self.journal.foundDefect(transaction, ['seo:huge_internal', size])
        return reqId


    def process_inline(self, transaction, style):
        #self.push_db(transactionId, style, "inline")
        if style in self.inlines_seen:
            self.duplicit_inline(transaction, style)
        else:
            self.inlines_seen.add(style)
        # TODO: testovat na podretezec 
        # TODO: zkoumat id/classy, zda tam neni podretezec inline css


    def duplicit_inline(self, transaction, style):
        self.journal.foundDefect(transaction, ['seo:duplicit_inline', style])
