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
            ## refactor after C++ proxy:
            #self.getLink(url, reqId)
        return

    def getId(self):
        return "linksFinder"

    def getLink(self, url, reqId):
        r = requests.get(url)
        self.database.setResponse(reqId, r.status_code, r.headers['content-type'], r.text.decode("UTF-8"), "")
