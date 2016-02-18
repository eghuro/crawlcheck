import unittest
import sqlite3 as mdb

from pluginDBAPI import DBAPIconfiguration
from pluginDBAPI import DBAPI
from plugin.py_w3c_html_validator_plugin import PyW3C_HTML_Validator


class PyW3cPluginTest(unittest.TestCase):
    def testSimpleFragment(_self):
        dbconf = DBAPIconfiguration()
        dbconf.setDbname('test.sqlite')

        api = DBAPI(dbconf)
        checker = PyW3C_HTML_Validator()
        checker.setDb(api)

        con = mdb.connect(dbconf.getDbname())
        cursor = con.cursor()

        cursor.execute("DELETE FROM transactions")
        cursor.execute('INSERT INTO transactions (id, method, uri, content, contentType, verificationStatusId, responseStatus, depth) VALUES (0, \'GET\', "http://kdmanalytics.com", ?, "text/html", 3, 200, 1)', [unicode(u'<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\"><html><head><title>KDM Analytics Inc.</title><meta http-equiv=\"REFRESH\" content=\"0;url=kdma/index.html\"></HEAD><BODY><center><a href=\"kdma/index.html\"><img src=\"/images/logo200px.png\" style=\"border-style: none;\"/></a></center></BODY></HTML>')])
        con.commit()

        transaction = api.getTransaction()
        checker.check(transaction.getId(), transaction.getContent())

if __name__ == '__main__':
    unittest.main()
