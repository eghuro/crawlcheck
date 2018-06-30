from yapsy.IPlugin import IPlugin
from tidylib import tidy_document
from common import PluginType
import logging


class Tidy_HTML_Validator(IPlugin):

    category = PluginType.CHECKER
    id = "tidyHtmlValidator"
    contentTypes = ["text/html"]

    def __init__(self):
        self.__journal = None
        self.__codes = dict()
        self.__max_err = 0
        self.__max_warn = 0
        self.__max_inf = 0
        self.__severity = dict()
        self.__severity['Warning'] = 0.5
        self.__severity['Error'] = 1.0
        self.__severity['Info'] = 0.3

    def setJournal(self, journal):
        self.__journal = journal

        maxes = {'W': self.__max_warn,
                 'E': self.__max_err,
                 'I': self.__max_inf}

        for dt in journal.getKnownDefectTypes():
            # dt[0] type, dt[1] description
            # parse codes of W{X} or E{Y} -> get max X or Y

            try:
                letter = dt[0][0]
                number = int(dt[0][1:])
                if letter in maxes:
                    if number > maxes[letter]:
                        maxes[letter] = number
                    self.__codes[dt[1]] = dt[0]
                else:
                    logging.getLogger(__name__).warn("Unknown letter: " +
                                                     letter)
            except ValueError:
                continue

    def check(self, transaction):
        res = tidy_document(transaction.getContent(), keep_doc=True)

        lines = res[1].splitlines()
        # lines is a list of strings that looks like:
        # line 54 column 37 - Warning: replacing invalid character code 153
        for line in lines:
            loc, desc = line.split(' - ', 1)
            err_warn, msg = desc.split(': ', 1)
            self.__record(transaction, loc, err_warn, msg)

    def __record(self, transaction, loc, cat, desc):
        code = self.__get_code(cat, desc)
        if cat in self.__severity:
            sev = self.__severity[cat]
        else:
            sev = -1.0
        self.__journal.foundDefect(transaction.idno, code, desc, [cat, loc],
                                   sev)

    def __generate_code(self, letter, number, desc):
        code = letter + str(number)
        self.__codes[desc] = code
        return code

    def __get_code(self, cat, desc):
        code = None
        if desc in self.__codes:
            code = self.__codes[desc]
        else:
            if cat == 'Warning':
                num = self.__max_warn
                self.__max_warn = self.__max_warn + 1
            elif cat == 'Error':
                num = self.__max_err
                self._max_err = self.__max_err + 1
            elif cat == 'Info':
                num = self.__max_inf
                self.__max_inf = self.__max_inf + 1
            else:
                log = logging.getLogger(__name__)
                log.error("Unknown category: " + cat)
                return None
            code = self.__generate_code(cat[0], num, desc)
        return code
