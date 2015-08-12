import unittest

from DBAPIconfiguration import DBAPIconfiguration
from pluginDBAPI import DBAPI
from py_w3c_html_validator_plugin import PyW3C_HTML_Validator

class PyW3cPluginTest(unittest.TestCase):
  def testSimpleFragment(_self):
    dbconf = DBAPIconfiguration()
    dbconf.setUri('localhost')
    dbconf.setUser('test')
    dbconf.setPassword('')
    dbconf.setDbname('crawlcheck')
    
    api = DBAPI(dbconf)
    checker = PyW3C_HTML_Validator(api)
    id = 0
    checker.check(id, "<html></html>")

if __name__ == '__main__':
  unittest.main()
