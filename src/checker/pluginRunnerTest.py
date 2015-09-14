import unittest

from pluginRunner import PluginRunner
from pluginDBAPI import DBAPIconfiguration
from pluginDBAPI import DBAPI
from plugin.py_w3c_html_validator_plugin import PyW3C_HTML_Validator
from plugin.links_finder_plugin import LinksFinder
from configLoader import ConfigLoader

class PluginRunnerTest(unittest.TestCase):

    def setUp(self):
        cl = ConfigLoader()
        cl.load('testConf.yml')
        self.dbconf = cl.getDbconf()
        self.typeacceptor = cl.getTypeAcceptor()
        self.uriacceptor = cl.getUriAcceptor()

        self.api = DBAPI(self.dbconf)

    def testRunW3C(self):
        w3c = PyW3C_HTML_Validator()

        runner = PluginRunner(self.dbconf, self.typeacceptor, self.uriacceptor, 1)
        runner.run([w3c])

    def testRunLinks(self):
        finder = LinksFinder()

        runner = PluginRunner(self.dbconf, self.typeacceptor, self.uriacceptor, 1)
        runner.run([finder])

    def testRunMultiple(self):
        w3c = PyW3C_HTML_Validator()
        finder = LinksFinder()

        runner = PluginRunner(self.dbconf, self.typeacceptor, self.uriacceptor, 1)
        runner.run([w3c, finder])

if __name__ == '__main__':
    unittest.main()
