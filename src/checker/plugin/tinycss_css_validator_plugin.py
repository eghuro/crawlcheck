import tinycss
from yapsy.IPlugin import IPlugin

class CssValidator(IPlugin):
    def __init__(self):
        self.database = None
    def setDb(self, DB):
        self.database = DB
    def getId(self):
        return "tinycss"
    def check(self, transactionId, content):
        parser = tinycss.make_parser('page3')
        stylesheet = parsre.parse_stylesheet(content)
        print stylesheet.errors
