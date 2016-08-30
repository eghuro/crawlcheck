from yapsy.IPlugin import IPlugin
from tidylib import tidy_document
from common import PluginType


class Tidy_HTML_Validator(IPlugin):
    
    category = PluginType.CHECKER
    id = "tidyHtmlValidator"

    def __init__(self):
        self.journal = None
        self.codes = dict() #TODO: preload existing error codes
        self.max_err = 0
        self.max_warn = 0

    def setJournal(self, journal):
        self.journal = journal

    def check(self, transaction):
        res = tidy_document(transaction.getContent(), keep_doc=True)

        lines = res[1].splitlines()
        #lines is a list of strings that looks like: line 54 column 37 - Warning: replacing invalid character code 153
        for line in lines:
            loc, desc = line.split(' - ', 1)
            err_warn, msg = desc.split(': ', 1)
            self.__record(transaction, loc, err_warn, msg)

    def __record(self, transaction, loc, cat, desc):
        code = self.__get_code(cat, desc)
        self.journal.foundDefect(transaction, code, desc, [cat, loc])

    def __generate_code(self, letter, number, desc):
        code = letter+str(number)
        self.codes[desc] = code
        return code

    def __get_code(self, cat, desc):
        code = None
        if desc in self.codes:
            code = self.codes[desc]
        else:
            if cat == 'Warning':
                num = self.max_warn
                self.max_warn = self.max_warn+1
            elif cat == 'Error':
                num = self.max_err
                self.max_err = self.max_err+1
            code = self.__generate_code(cat[0], num, desc)
        return code
