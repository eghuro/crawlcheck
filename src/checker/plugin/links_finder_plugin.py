from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin
import requests

class LinksFinder(IPlugin):

    def __init__(self):
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def check(self, transactionId, content):
        soup = BeautifulSoup(content, 'html.parser')
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
