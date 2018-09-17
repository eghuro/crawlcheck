from yapsy.IPlugin import IPlugin
from tidylib import tidy_document
import logging
import redis
try:
    from crawlcheck.checker.common import PluginType
except ImportError:
    from common import PluginType


class Tidy_HTML_Validator(IPlugin):

    category = PluginType.CHECKER
    id = "tidyHtmlValidator"
    contentTypes = ["text/html"]

    def __init__(self):
        self.__journal = None
        self.__severity = dict()
        self.__severity['Warning'] = 0.5
        self.__severity['Error'] = 1.0
        self.__severity['Info'] = 0.3
        self.__redis = None

    def setConf(self, conf):
        self.__redis = redis.StrictRedis(host=conf.getProperty('redisHost', 'localhost'),
                                         port=conf.getProperty('redisPort', 6379),
                                         db=conf.getProperty('redisDb', 0))


    def setJournal(self, journal):
        self.__journal = journal

        maxes = {'W': self.__redis.get('tidyMaxWarn'),
                 'E': self.__redis.get('tidyMaxErr'),
                 'I': self.__redis.get('tidyMaxInfo'),
                 'X': self.__redis.get('tidyMaxUnknown')}

        for dt in journal.getKnownDefectTypes():
            # dt[0] type, dt[1] description
            # parse codes of W{X} or E{Y} -> get max X or Y

            try:
                letter = dt[0][0]
                number = int(dt[0][1:])
                if letter in maxes:
                    if number > maxes[letter]:
                        maxes[letter] = number
                    self.__redis.hset('tidyCodes', dt[1], dt[0])
                else:
                    logging.getLogger(__name__).warn("Unknown letter: " +
                                                     letter)
            except ValueError:
                logging.getLogger(__name__).exception("Code not found")
                continue

    def check(self, transaction):
        res = tidy_document(transaction.getContent(), keep_doc=True)

        lines = res[1].splitlines()
        # lines is a list of strings that looks like:
        # line 54 column 37 - Warning: replacing invalid character code 153
        # Warning: adjacent hyphens within comment
        for line in lines:
            if not '-' in line:
                err_warn, msg = line.split(':', 1)
                self.__record(transaction, None, err_warn.strip(), msg.strip())
            else:
                try:
                    loc, desc = line.split(' - ', 1)
                    err_warn, msg = desc.split(': ', 1)
                    self.__record(transaction, loc, err_warn.strip(), msg.strip())
                except:
                    try:
                        loc, desc = line.split('-')
                        err_warn, msg = desc.split(':', 1)
                        if len(msg.strip()) == 0:
                            logging.getLogger(__name__).warning("No description! Line was: %s" % line)
                            msg = "Generic HTML syntax " + err_warn.to_lower()
                        self.__record(transaction, loc, err_warn.strip(), msg.strip())
                    except ValueError:
                        logging.getLogger(__name__).exception("Failed to parse result! Line was: %s" % line)

    def __record(self, transaction, loc, cat, desc):
        code = self.__get_code(cat, desc)
        if cat in self.__severity:
            sev = self.__severity[cat]
        else:
            sev = -1.0
        self.__journal.foundDefect(transaction.idno, code, desc, [cat, loc],
                                   sev)

    def __get_code(self, cat, desc):
        if self.__redis.hexists('tidyCodes', desc):
            code = self.__redis.hget('tidyCodes', desc)
        else:
            if cat == 'Warning':
                num = self.__redis.incr('tidyMaxWarn')
            elif cat == 'Error':
                num = self.__redis.incr('tidyMaxErr')
            elif cat == 'Info':
                num = self.__redis.incr('tidyMaxInfo')
            else:
                log = logging.getLogger(__name__)
                log.error("Unknown category: " + cat)
                cat = 'X'
                num = self.__redis.incr('tidyMaxUnknown')
            code = cat[0] + str(num)
            self.__redis.hset('tidyCodes', desc, code)
        return code
