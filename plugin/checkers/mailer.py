try:
    from crawlcheck.checker.common import PluginType, getSoup
except ImportError:
    from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin
from validate_email import validate_email
import functools
import re


class Mailer(IPlugin):

    category = PluginType.CHECKER
    id = "mailer"
    contentTypes = ["text/html"]

    __severities = [0.3, 0.8, 0.9, 1.0]

    def __init__(self):
        pass

    def setJournal(self, journal):
        self.__journal = journal

    def setConf(self, conf):
        self.__mx = conf.getProperty('mailer.mx', False)
        self.__exists = conf.getProperty('mailer.exists', False)
        self.__full = conf.getProperty('mailer.full', False)

    def check(self, transaction):
        if not self.__full:
            soup = getSoup(transaction)
            for link in soup.find_all('a'):
                self.__check_link(link, transaction)
        else:
            # see: https://stackoverflow.com/questions/17681670/extract-email-sub-strings-from-large-document#17681902
            for e in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', transaction.getContent()):
                self.__process(transaction, e, "mail: " + str(e))
        return

    def __check_link(self, link, transaction):
        url = link.get('href')
        if url is not None:
            if url.startswith('mailto:'):
                self.__process(transaction, link['href'][7:], "Link: " + str(link))


    def __process(self, transaction, mail, intro):
        is_valid, mx, verify = self.__validate(mail)
        severity = Mailer.__severities[sum([int(is_valid), int(mx), int(verify)])]
        description = intro + ", valid: " + str(is_valid) + " (checked SMTP server: " + str(mx) + ", verified existence: " + str(verify) + ")"
        self.__journal.foundDefect(transaction.idno, 'mail', 'Found e-mail', description, severity)


    @functools.lru_cache()
    def __validate(self, mail):
        if self.__exists:
            v = validate_email(mail, verify=True)
            if v is not None:
                return v, True, True
        if self.__mx or self.__exists:
            v = validate_email(mail, check_mx=True)
            if v is not None:
                return v, True, False
        return validate_email(mail), False, False
