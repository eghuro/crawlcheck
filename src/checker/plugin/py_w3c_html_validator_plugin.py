from common import PluginType
from yapsy.IPlugin import IPlugin
from py_w3c.validators.html.validator import HTMLValidator
from py_w3c.exceptions import ValidationFault
from urllib2 import HTTPError, URLError
import time


class PyW3C_HTML_Validator(IPlugin):
    
    type = PluginType.CHECKER
    id = "htmlValidator"
    
    
    def __init__(self):
        self.validator = HTMLValidator()
        self.journal = None

    def setJournal(self, journal):
        self.journal = journal

    def check(self, transaction):
        """ Pusti validator, ulozi chyby a varovani.
        """
        content = transaction.getContent()
        try:
            self.validator.validate_fragment(content)
            self.check_errors(transaction)
            self.check_warnings(transaction)
            time.sleep(3)
        except ValidationFault as e:
            print("Validation fault")
        except HTTPError as e:
            print("HTTP Error "+str(e.code)+": "+str(e.reason))
        except URLError as e:
            print("Connection problem: "+str(e.reason))
        except Exception as e:
            print("Unexpected problem: "+str(type(e)))
        return

    def transformMessageId(self, mid, mtype):
        return self.getId()+":"+mtype+":"+mid

    def check_errors(self, transaction):
        self.check_defects(transaction, self.validator.errors, "err")

    def check_warnings(self, transaction):
        self.check_defects(transaction, self.validator.warnings, "warn")

    def check_defects(self, transaction, defects, message):
        for defect in defects:
            mid = self.transformMessageId(defect['messageid'], message)
            self.journal.foundDefect(transaction, [mid, defect['message'], defect['line'], defect['source']] #TODO: refactor DB?
