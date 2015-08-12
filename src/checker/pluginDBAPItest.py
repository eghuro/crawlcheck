import unittest
from checker.pluginDBAPI import DBAPI
from checker.pluginDBAPI import DBAPIconfiguration

class DBAPITest(unittest.TestCase):
    def setUp(self):
        self.conf = DBAPIconfiguration()
        self.conf.setUri('localhost')
        self.conf.setUser('test')
        self.conf.setPassword('')
        self.conf.setDbname('crawlcheck')

    def testInstance(self):
        DBAPI(self.conf)

    def testGetTransaction(self):
        api = DBAPI(_self.conf)
        tr = api.getTransaction()
        assert tr.getId() == -1
        assert tr.getContent() == ""

if __name__ == '__main__':
    unittest.main()


