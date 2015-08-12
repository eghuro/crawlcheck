import unittest

from pluginRunner import PluginRunner
from DBAPIconfiguration import DBAPIconfiguration
from pluginDBAPI import DBAPI
from py_w3c_html_validator_plugin import PyW3C_HTML_Validator

class PluginRunnerTest(unittest.TestCase):
    def testRunW3C(self):
        dbconf = DBAPIconfiguration()
        dbconf.setUri('localhost')
        dbconf.setUser('test')
        dbconf.setPassword('')
        dbconf.setDbname('crawlcheck')
    
        api = DBAPI(dbconf)
        w3c = PyW3C_HTML_Validator(api)

        runner = PluginRunner(api)
        runner.run(w3c)

if __name__ == '__main__':
    unittest.main()
