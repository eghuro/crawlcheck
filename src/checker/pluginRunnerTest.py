import unittest

from checker.pluginRunner import PluginRunner
from checker.pluginDBAPI import DBAPIconfiguration
from checker.pluginDBAPI import DBAPI
from checker.plugin.py_w3c_html_validator_plugin import PyW3C_HTML_Validator
from checker.plugin.links_finder_plugin import LinksFinder

class PluginRunnerTest(unittest.TestCase):

    def setUp(self):
        self.dbconf = DBAPIconfiguration()
        self.dbconf.setUri('localhost')
        self.dbconf.setUser('test')
        self.dbconf.setPassword('')
        self.dbconf.setDbname('crawlcheck')

        self.api = DBAPI(self.dbconf)

    def testRunW3C(self):
        w3c = PyW3C_HTML_Validator()

        runner = PluginRunner(self.dbconf)
        runner.run([w3c])

    def testRunLinks(self):
        finder = LinksFinder()

        runner = PluginRunner(self.dbconf)
        runner.run([finder])

    def testRunMultiple(self):
        w3c = PyW3C_HTML_Validator()
        finder = LinksFinder()

        runner = PluginRunner(self.dbconf)
        runner.run([w3c, finder])

if __name__ == '__main__':
    unittest.main()
