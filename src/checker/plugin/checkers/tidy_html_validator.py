from yapsy.IPlugin import IPlugin
from tidylib import tidy_document
from common import PluginType


class Tidy_HTML_Validator(IPlugin):
    
    category = PluginType.CHECKER
    id = "tidyHtmlValidator"

    def __init__(self):
        self.journal = None
        self.codes = dict()
        self.max_err = 0
        self.max_warn = 0
        self.severity = dict()
        self.severity['Warning'] = 0.5
        self.severity['Error'] = 1.0

    def setJournal(self, journal):
        self.journal = journal

        #for dt in journal.getKnownDefectTypes(): #TODO: TESTME
        #    #dt[0] type, dt[1] description
        #    #parse codes of W{X} or E{Y} -> get max X or Y
            
        #    letter = dt[0][0]
        #    number = int(dt[0][1:])
        #    if letter == 'W':
        #        if number > self.max_warn:
        #            self.max_warn = number
        #        self.codes[dt[1]] = dt[0]
        #    elif letter == 'E':
        #        if number > self.max_err:
        #            self.max_err = number
        #        self.codes[dt[1]] = dt[0]

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
        if cat in self.severity:
            sev = self.severity[cat]
        else:
            sev = -1.0
        self.journal.foundDefect(transaction.idno, code, desc, [cat, loc], sev)

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
