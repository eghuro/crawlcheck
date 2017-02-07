from common import PluginType
import core
from yapsy.IPlugin import IPlugin
from bs4 import BeautifulSoup
import urllib.parse

class Form_Checker(IPlugin):

    category = PluginType.CRAWLER
    id = "formChecker"

    def __init__(self):
        self.queue = None

    def setJournal(self, journal):
        pass

    def setQueue(self, queue):
        self.queue = queue

    def check(self, transaction):
        soup = BeautifulSoup(transaction.getContent().encode('utf-8'), 'html.parser')
        forms = soup.find_all('form')
        for form in forms:
            self.check_form(form, transactionId)

    def check_form(self, form, transactionId):
        method = self.get_method(form)
        action = self.get_action(form, transactionId)
        params = self.get_params(form)

        self.queue.push(core.createTransaction(action, transaction.depth+1), transaction)
        #self.database.setScript(transactionId, action, method, params)
        # TODO: script
        # TODO: params

    def get_method(self, form):
        if 'method' in form.attrs:
            return form['method'].to_upper()
        else:
            return 'GET'

    def get_action(self, form, transactionId): 
        base = self.database.getUri(transactionId)
        if 'action' in form.attrs:
            return urllib.parse.urljoin(base, form['action'])
        else:
            return base

    def get_params(self, form):
        params = []
        inputs = form.find_all('input')
        for field in inputs:
            if name in field.attrs:
                params.insert(field['name'])
        # TODO: zachytavat i mozne hodnoty
        return params
