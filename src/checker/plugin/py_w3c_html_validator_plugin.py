from yapsy.IPlugin import IPlugin
from py_w3c.validators.html.validator import HTMLValidator
from py_w3c.exceptions import ValidationFault
from urllib2 import HTTPError, URLError
import time


class PyW3C_HTML_Validator(IPlugin):
    def __init__(self):
        self.validator = HTMLValidator()
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def check(self, transactionId, content):
        """ Pusti validator, ulozi chyby a varovani.
        """
        try:
            self.validator.validate_fragment(content)
            self.check_errors(transactionId)
            self.check_warnings(transactionId)
            time.sleep(3)
        except ValidationFault as e:
            print("Validation fault")
        except HTTPError as e:
            print("HTTP Error "+str(e.code)+": "+str(e.reason))
        except URLError as e:
            print("Connection problem: "+str(e.reason))
        # except Exception as e:
        #    print("Unexpected problem: "+str(type(e)))
        return

    def getId(self):
        return "htmlValidator"

    def transformMessageId(self, mid, mtype):
        return self.getId()+":"+mtype+":"+mid

    def check_errors(self, transactionId):
        self.check_defects(transactionId, self.validator.errors, "err")

    def check_warnings(self, transactionId):
        self.check_defects(transactionId, self.validator.warnings, "warn")

    def check_defects(self, transactionId, defects, message):
        for defect in defects:
            mid = self.transformMessageId(defect['messageid'], message)
            self.database.putNewDefectType(mid, defect['message'])
            self.database.setDefect(transactionId, mid, defect['line'], defect['source'])
