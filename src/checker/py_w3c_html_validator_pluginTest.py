import unittest
import MySQLdb as mdb

from pluginDBAPI import DBAPIconfiguration
from pluginDBAPI import DBAPI
from plugin.py_w3c_html_validator_plugin import PyW3C_HTML_Validator

class PyW3cPluginTest(unittest.TestCase):
  def testSimpleFragment(_self):
    dbconf = DBAPIconfiguration()
    dbconf.setUri('localhost')
    dbconf.setUser('test')
    dbconf.setPassword('')
    dbconf.setDbname('crawlcheck')
    
    api = DBAPI(dbconf)
    checker = PyW3C_HTML_Validator()
    checker.setDb(api)

    con = mdb.connect(dbconf.getUri(), dbconf.getUser(), dbconf.getPassword(), dbconf.getDbname())
    cursor = con.cursor()
    
    cursor.execute("DELETE FROM transaction")
    cursor.execute('INSERT INTO transaction (id, method, uri, content, contentType, verificationStatusId, responseStatus) VALUES (0, \'GET\', "http://kdmanalytics.com", \"' + con.escape_string("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\"><html><head><title>KDM Analytics Inc.</title><meta http-equiv=\"REFRESH\" content=\"0;url=kdma/index.html\"></HEAD><BODY><center><a href=\"kdma/index.html\"><img src=\"/images/logo200px.png\" style=\"border-style: none;\"/></a></center></BODY></HTML>") +'\", "text/html", 3, 200)')
    con.commit()

    transaction = api.getTransaction()
    checker.check(transaction.getId(), transaction.getContent())

if __name__ == '__main__':
  unittest.main()
