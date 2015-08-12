from yapsy.IPlugin import IPlugin
from py_w3c.validators.html.validator import HTMLValidator

class PyW3C_HTML_Validator(IPlugin):
    def __init__(self):
        self.validator = HTMLValidator()
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def check(self, transactionId, content):
        self.validator.validate_fragment(content)
        # print _self.validator.errors
        for error in self.validator.errors:
            self.database.setDefect(transactionId,
                                    self.transformMessageId(error['messageid']),
                                    error['line'], error['source'])

            print self.validator.warnings
        return

    def handleContent(self, contentType):
        if contentType == "text/html":
            return True
        return False

    def transformMessageId(self, mid):
        return mid
