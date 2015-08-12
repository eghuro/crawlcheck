from bs4 import BeautifulSoup
from yapsy.IPlugin import IPlugin

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

            self.database.setLink(transactionId, url)
        return

    def handleContent(self, contentType):
        return contentType == "text/html" 
