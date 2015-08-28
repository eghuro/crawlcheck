from yapsy.IPlugin import IPlugin
from py_w3c.validators.html.validator import HTMLValidator
from py_w3c.exceptions import ValidationFault

class PyW3C_HTML_Validator(IPlugin):
    def __init__(self):
        self.validator = HTMLValidator()
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def check(self, transactionId, content):
        try:
            self.validator.validate_fragment(content)
            for error in self.validator.errors:
                self.database.putNewDefectType(self.transformMessageId(error['messageid'], "err"), error['message'])
                self.database.setDefect(transactionId,
                                        self.transformMessageId(error['messageid'], "err"),
                                        error['line'], error['source'])

            for warning in self.validator.warnings:
                 self.database.putNewDefectType(self.transformMessageId(warning['messageid'], "warn"), warning['message'])
                 self.database.setDefect(transactionId,
                                         self.transformMessageId(warning['messageid'], "warn").
                                         warning['line'], warning['source'])
        except ValidationFault:
            print "Validation error"
        return

    def getId(self):
        return "htmlValidator"

    def transformMessageId(self, mid, mtype):
        return self.getId()+":"+mtype+":"+mid
