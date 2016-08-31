from common import PluginType
from yapsy.IPlugin import IPlugin
from py_w3c.validators.html.validator import HTMLValidator
from py_w3c.exceptions import ValidationFault
from urllib.error import HTTPError, URLError
import time
import logging


class PyW3C_HTML_Validator(IPlugin):
    
    category = PluginType.CHECKER
    id = "htmlValidator"
    MAX_COUNT = 80
    DELAY = 3
    
    
    def __init__(self):
        self.validator = HTMLValidator()
        self.journal = None
        self.count = 0

    def setJournal(self, journal):
        self.journal = journal

    def check(self, transaction):
        """ Pusti validator, ulozi chyby a varovani.
        """
        content = transaction.getContent()
        log = logging.getLogger()
        try:
            self.validator.validate_fragment(content) ##this takes too long
            self.check_errors(transaction)
            self.check_warnings(transaction)

            self.count = self.count + 1
            log.debug("counter: "+str(self.count))
            if self.count == PyW3C_HTML_Validator.MAX_COUNT:
                log.debug("Sleep")
                time.sleep(PyW3C_HTML_Validator.DELAY)
                self.count = 0
        except ValidationFault as e:
            log.debug("Validation fault: "+format(e))
        except HTTPError as e:
            log.debug("HTTP Error "+str(e.code)+": "+str(e.reason))
        except URLError as e:
            log.debug("Connection problem: "+str(e.reason))
        except Exception as e:
            log.debug("Unexpected problem: "+str(type(e)))
        return

    def transformMessageId(self, mid, mtype):
        return self.id+":"+mtype+":"+mid

    def check_errors(self, transaction):
        self.check_defects(transaction, self.validator.errors, "err")

    def check_warnings(self, transaction):
        self.check_defects(transaction, self.validator.warnings, "warn")

    def check_defects(self, transaction, defects, message):
        for defect in defects:
            mid = self.transformMessageId(defect['messageid'], message)
            self.journal.foundDefect(transaction.idno, mid, None, [defect['message'], defect['line'], defect['source']])
