from yapsy.IPlugin import IPlugin
from bs4 import BeautifulSoup
import urlparse

class Form_Checker(IPlugin):
    def __init__(self):
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def check(self, transactionId, content):
        soup = BeautifulSoup(content, 'html.parser')
        forms = soup.find_all('form')
        for form in forms:
            self.check_form(form, transactionId)

    def check_form(self, form, transactionId):
        method = self.get_method(form)
        action = self.get_action(form, transactionId)

    def get_method(self, form):
        if 'method' in form.attrs:
            return form['method'].to_lower()
        else:
            return 'get'

    def get_action(self, form, transactionId): 
        base = self.database.getUri(transactionId)
        if 'action' in form.attrs:
            return urlparse.urljoin(base, form['action'])
        else:
            return base

    def getId(self):
        return "formChecker"
