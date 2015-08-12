import unittest

from pluginRunner import PluginRunner
from DBAPIconfiguration import DBAPIconfiguration
from pluginDBAPI import DBAPI
from py_w3c_html_validator_plugin import PyW3C_HTML_Validator
from links_finder_plugin import LinksFinder

class PluginRunnerTest(unittest.TestCase):

    def setUp(self):
       self.dbconf = DBAPIconfiguration()
       self.dbconf.setUri('localhost')
       self.dbconf.setUser('test')
       self.dbconf.setPassword('')
       self.dbconf.setDbname('crawlcheck')

       self.api = DBAPI(self.dbconf)

    def testRunW3C(self):
        w3c = PyW3C_HTML_Validator(self.api)

        runner = PluginRunner(self.api)
        runner.run(w3c)

    def testRunLinks(self):
        finder = LinksFinder(self.api)

        runner = PluginRunner(self.api)
        runner.run(finder)

    def testRunMultiple(self):
        w3c = PyW3C_HTML_Validator(self.api)
        finder = LinksFinder(self.api)
    
        runner = PluginRunner(self.api)
        runner.run(w3c, finder)

if __name__ == '__main__':
    unittest.main()
