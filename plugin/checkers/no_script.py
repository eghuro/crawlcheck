try:
    from crawlcheck.checker.common import PluginType, getSoup
except ImportError:
    from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin
from bs4.element import Comment


class NoScript(IPlugin):

    category = PluginType.CHECKER
    id = "noscript"
    contentTypes = ["text/html"]

    def __init__(self):
        pass

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        soup = getSoup(transaction)
        for script in soup.body.find_all('script'):
            if script.next_sibling is None or script.next_sibling.name != 'noscript':
                dsc = " ".join(["Script:", str(script), "\nNext sibling:", str(script.next_sibling)])
                self.__journal.foundDefect(transaction.idno, 'noscript-miss',
                                           '<script> tag is not followed by <noscript>',
                                           dsc, 0.7)

            if not isinstance(script.string, Comment):
                self.__journal.foundDefect(transaction.idno, 'script-no-comment',
                                           'Content of <script> is not in HTML comment',
                                           "Script: " + str(script), 0.4)
        return
