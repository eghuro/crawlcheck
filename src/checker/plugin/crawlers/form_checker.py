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
        if 'soup' in transaction.cache and transaction.cache['soup']:
            soup = transaction.cache['soup']
        else:
            soup = BeautifulSoup(transaction.getContent(), 'lxml')
            transaction.cache['soup'] = soup
        forms = soup.find_all('form')
        for form in forms:
            self.check_form(form, transaction)

    def check_form(self, form, transaction):
        method = self.get_method(form)
        action = self.get_action(form, transaction)
        params = self.get_params(form)

        self.queue.push(core.createTransaction(action, transaction.depth+1), transaction)
        #self.database.setScript(transactionId, action, method, params)
        # TODO: script
        # TODO: params

    def get_method(self, form):
        if 'method' in form.attrs:
            return form['method'].upper()
        else:
            return 'GET'

    def get_action(self, form, transaction):
        base = transaction.uri
        if 'action' in form.attrs:
            return urllib.parse.urljoin(base, form['action'])
        else:
            return base

    def get_params(self, form):
        params = []
        inputs = form.find_all('input')
        for field in inputs:
            if 'name' in field.attrs:
                params.append(field['name'])
        # TODO: zachytavat i mozne hodnoty
        return params
