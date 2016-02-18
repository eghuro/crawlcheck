import tinycss
from yapsy.IPlugin import IPlugin


class CssValidator(IPlugin):
    def __init__(self):
        self.database = None

    def setDb(self, DB):
        self.database = DB

    def getId(self):
        return "tinycss"

    def check(self, transactionId, content):
        """Pusti validator, ulozi chyby.
        """
        try:
            parser = tinycss.make_parser('page3')
            stylesheet = parser.parse_stylesheet(content)
            for error in stylesheet.errors:
                self.database.setDefect(transactionId, "stylesheet", error.line, error.reason)
        except UnicodeDecodeError:
            print("Error")
        return
