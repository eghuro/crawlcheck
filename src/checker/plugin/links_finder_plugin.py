from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
import requests
import urlparse

class LinksFinder(IPlugin):

    def __init__(self):
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def check(self, transactionId, content):
        soup = BeautifulSoup(content, 'html.parser')
        self.make_links_absolute(soup, self.database.getUri(transactionId))
        links = soup.find_all('a')
        for link in links:
            url = link.get('href')

            reqId = self.database.setLink(transactionId, url)
            self.getLink(url, reqId)
        return

    def getId(self):
        return "linksFinder"

    def getLink(self, url, reqId):
        print "Downloading "+url
        r = requests.get(url)
        self.database.setResponse(reqId, r.status_code, r.headers['content-type'], r.text.encode("utf-8").strip()[:65535])

    def make_links_absolute(self, soup, url):
        for tag in soup.findAll('a', href=True):
            tag['href'] = urlparse.urljoin(url, tag['href'])
