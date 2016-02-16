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
        self.runPlugins([PyW3C_HTML_Validator()])

    def testRunLinks(self):
        self.runPlugins([LinksFinder()])

    def runPlugins(self, plugins):
        runner = PluginRunner(self.dbconf, self.typeacceptor, self.uriacceptor, 1)
        runner.run(plugins)

    def testRunMultiple(self):
        self.runPlugins([PyW3C_HTML_Validator(), LinksFinder()])

    def testTransaction(self):
        #vlozit cosi do DB

        self.testRunMultiple()

if __name__ == '__main__':
    unittest.main()
