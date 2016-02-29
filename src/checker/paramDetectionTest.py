import unittest
import sqlite3 as mdb
from pluginDBAPI import DBAPI
from pluginDBAPI import DBAPIconfiguration

class DBAPItest(unittest.TestCase):
    def setUp(self):
        c = DBAPIconfiguration()
        c.setDbname('test.sqlite')
        self.api = DBAPI(c)

        self.con = mdb.connect(c.getDbname())
        self.cursor = self.con.cursor()

    def testUsecaseForm(self):
        self.cleanDb()
        trId = self.insertTransaction()

        self.usecaseForm(trId)
        
        self.cursor.execute('SELECT count(responseId) from finding')
        self.assertEqual(3, self.cursor.fetchone()[0])

        self.cursor.execute('SELECT count(findingId) from link')
        self.assertEqual(1, self.cursor.fetchone()[0])

        self.cursor.execute('SELECT responseId FROM finding')
        self.assertEqual(trId, self.cursor.fetchone()[0])
        self.assertEqual(trId, self.cursor.fetchone()[0])

        self.cursor.execute('SELECT toUri FROM link')
        self.assertEqual('script.php', self.cursor.fetchone()[0])

        self.cursor.execute('SELECT count(id) FROM parameter')
        self.assertEqual(2, self.cursor.fetchone()[0])

        self.cursor.execute('SELECT count(findingId) FROM scriptAction')
        self.assertEqual(2, self.cursor.fetchone()[0])

    def usecaseForm(self, trId):
        #zpracovavame transakci trId
        #nasli jsme formular mirici na script.php metodou POST
        #formular obsahuje jeden label name a jeden hidden check
        self.api.setForm(trId, 'script.php')
        self.api.setScript(trId, 'script.php', 'POST',  ['name', 'check'])

    def testUsecaseLinkWithParams(self):
        self.cleanDb()
        trId = self.insertTransaction()

        self.usecaseLinkWithParams(trId, 1)

    def usecaseLinkWithParams(self, trId, depth):
        #nalezli jsme odkaz na script.php?name=Bobbby&check=false
        self.api.setLink(trId, 'script.php?name=Bobby&check=false', depth)
        self.api.setScript(trId, 'script.php', 'GET', ['name', 'check'])
        self.api.setParams('script.php', 'name', 'Bobby')
        self.api.setParams('script.php', 'check', 'false')

    def cleanDb(self):
        a = ('DELETE FROM finding')
        b = ('DELETE FROM link')
        c = ('DELETE FROM parameter')
        d = ('DELETE FROM scriptAction')

        self.cursor.execute(a)
        self.cursor.execute(b)
        self.cursor.execute(c)
        self.cursor.execute(d)
        
        self.con.commit()

    def insertTransaction(self):
        self.cursor.execute('INSERT INTO transactions (method, uri, origin, '
                            'verificationStatusId, depth) VALUES ("GET", "/", '
                            '"CHECKER", 1, 0)')
        trid = self.cursor.lastrowid
        self.con.commit()
        return trid

if __name__ == '__main__':
    unittest.main()
