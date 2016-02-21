from yapsy.IPlugin import IPlugin

class Form_Checker(IPlugin):
    def __init__(self):
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def check(self, transactionId, content):
        pass

    def getId(self):
        return "formChecker"
