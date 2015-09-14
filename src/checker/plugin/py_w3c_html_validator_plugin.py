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
            time.sleep(3)
        except ValidationFault, e:
            print "Validation fault"
        except HTTPError, e:
            print "HTTP Error "+str(e.code)+": "+str(e.reason)
        except URLError, e:
            print "Connection problem: "+str(e.reason) 
        except Exception as e:
            print "Unexpected problem"
        return
    def getId(self):
        return "htmlValidator"

    def transformMessageId(self, mid, mtype):
        return self.getId()+":"+mtype+":"+mid
