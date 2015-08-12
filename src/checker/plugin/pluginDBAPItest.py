import unittest
from pluginDBAPI import DBAPI
from DBAPIconfiguration import DBAPIconfiguration

class DBAPITest(unittest.TestCase):
  def setUp(_self):
    _self.conf = DBAPIconfiguration()
    _self.conf.setUri('localhost')
    _self.conf.setUser('test')   
    _self.conf.setPassword('')
    _self.conf.setDbname('crawlcheck')

  def testInstance(_self):
    api = DBAPI(_self.conf)

  def testGetTransaction(_self):
    api = DBAPI(_self.conf)
    tr = api.getTransaction()
    assert tr.getId() == -1
    assert tr.getContent() == ""

if __name__ == '__main__':
    unittest.main()


