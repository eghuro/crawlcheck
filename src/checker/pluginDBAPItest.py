#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest
import sqlite3 as mdb

from pluginDBAPI import DBAPI
from pluginDBAPI import DBAPIconfiguration
from pluginDBAPI import TransactionInfo
from configLoader import ConfigLoader


class TransactionInfoTest(unittest.TestCase):
    def setUp(self):
        self.ti = TransactionInfo(0, None, '', "http://foobar.org", 36656)

    def testId(self):
        self.assertEqual(self.ti.getId(), 0)

    def testGetContent(self):
        self.assertEqual(self.ti.getContent(), None)

    def testGetContentType(self):
        self.assertEqual(self.ti.getContentType(), '')

    def testGetUri(self):
        self.assertEqual(self.ti.getUri(), "http://foobar.org")

    def testGetDepth(self):
        self.assertEqual(self.ti.getDepth(), 36656)

class DBAPITest(unittest.TestCase):
    def setUp(self):
        cl = ConfigLoader()
        cl.load('testConf.yml')
        self.conf = cl.getDbconf()
        self.maxDiff = None

    def testInstance(self):
        DBAPI(self.conf)

    def testGetTransactionEmptyDb(self):
        con = mdb.connect(self.conf.getDbname())
        cursor = con.cursor()
        cursor.execute("DELETE FROM transactions")
        con.commit()

        api = DBAPI(self.conf)
        tr = api.getTransaction()
        self.assertEqual(tr.getId(), -1)
        self.assertEqual(tr.getContent(), "")
        self.assertEqual(tr.getContentType(), "")

        con.close()

    def testGetTransactionNonEmptyDb(self):
        con = mdb.connect(self.conf.getDbname())
        cursor = con.cursor()
        cursor.execute("DELETE FROM transactions")
        response = ('<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n<title>408 Request Timeout</title>\n</head><body>\n<h1>Request Timeout</h1>\n<p>Server timeout waiting for the HTTP request from the client.</p>\n<hr>\n<address>Apache/2.4.10 (Debian) Server at olga.majling.eu Port 80</address>\n</body></html>')
        cursor.execute("INSERT INTO transactions (id, method, uri, responseStatus, contentType, content, verificationStatusId, depth) VALUES (1, 'GET', \"http://olga.majling.eu/Vyuka\", 200, \"text/html; charset=iso-8859-1\",?, 3, 1)", [response])

        con.commit()

        api = DBAPI(self.conf)
        tr = api.getTransaction()

        self.assertEqual(tr.getId(), 1)
        self.assertEqual(tr.getContent(), response)
        self.assertEqual(tr.getContentType(), "text/html")

        con.close()

    def testGetTransactionOutOfMultiple(self):
        con = mdb.connect(self.conf.getDbname())
        cursor = con.cursor()
        cursor.execute("DELETE FROM transactions")
        response = ('<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n<title>408 Request Timeout</title>\n</head><body>\n<h1>Request Timeout</h1>\n<p>Server timeout waiting for the HTTP request from the client.</p>\n<hr>\n<address>Apache/2.4.10 (Debian) Server at olga.majling.eu Port 80</address>\n</body></html>')
        cursor.execute("INSERT INTO transactions (id, method, uri, responseStatus, contentType, content, verificationStatusId, depth) VALUES (1, 'GET', \"http://olga.majling.eu/Vyuka\", 200, \"text/html; charset=iso-8859-1\",?, 3, 1)", [response])
        con.commit()

        response2 = ('<!--\nOlga Majlingová website is licenced under Affero General Public Licence (http://www.fsf.org/licensing/licenses/agpl-3.0.html) \n(c)Alexander Mansurov, 2010\n-->\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0\n'
                     ' Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="cs">\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
                     '\n<meta http-equiv="Content-Language" content="cs" />\n<meta name="copyright" content="&copy;Olga Majlingova, 2010" />\n<meta name="author" content="Alexander Mansurov" />\n'
                     '<meta name="description" content="Stranky Olgy Majlingove. Informace o vyuce" />\n<meta name="keywords" content="Olga, Majlingova, numericka, matematika, ZAPG, algoritmizace, programovani, CVUT, strojni" />\n'
                     '<title>Olga Majlingová</title>\n<link rel="stylesheet" type="text/css" href="http://olga.majling.eu/style.css" />\n<link href="http://olga.majling.eu/favicon.ico" rel="icon" type="icon" />\n'
                     '<meta name="google-site-verification" content="wvcZggg6XWngknlmp1t3bSDD-q67LDDoq2n-K6wEKgg" />\n<link href="http://olga.majling.eu/novinky.rss" rel="alternate" type="application/rss+xml" title="RSS kanál" />\n'
                     '<meta name="Robots" content="index,follow" />\n</head>\n<body>\n<table border="0" align="center" width="100%">\n<tr><td class="table-up hightab"><div align="left"><a href="http://www3.fs.cvut.cz/web/">\n'
                     '<img src="http://olga.majling.eu/img/cvut-logo-pr0.gif" width="100" height="100" alt="CVUT" border="0"/></a></div>\n</td><td class="table-up hightab"><div align="center"><h1>Olga Majlingová</h1>'
                     '<p class="desc">Ústav technické matematiky, FS ČVUT</p></div></td>\n<td class="table-up hightab"><div align="right"><a href="http://olga.majling.eu/">\n<img src="http://olga.majling.eu/img/OM5a.gif" width="95"\n'
                     'height="100" alt="foto" border="0"/></a></div><!--</td></tr></table></div>--></td></tr>\n<tr><td class="upL" rowspan="2" width="25%">\n<a href="http://olga.majling.eu/">'
                     '<img src="http://olga.majling.eu//img/Úvod.gif" alt="Úvod" border="0"/></a><br />\n<a href="http://olga.majling.eu/Vyuka"><img src="http://olga.majling.eu//img/Výuka.gif" border="0" alt="Výuka"/></a><br />\n'
                     '<ul>\n<li><a href="http://olga.majling.eu/Vyuka/Matematika-3">Matematika 3</a></li>\n<li><a href="http://olga.majling.eu/Vyuka/Matematika-1">Matematika 1</a></li>\n'
                     '<li><a href="http://olga.majling.eu/Vyuka/ZAPG">ZAPG</a></li>\n<li><a href="http://olga.majling.eu/Vyuka/Numericka-matematika">Numerická matematika</a></li>\n<li><a href="http://olga.majling.eu/Vyuka/\n'
                     'Matematika-2">Matematika 2</a></li>\n</ul>\n<a href="http://olga.majling.eu/UJEP">UJEP</a><br />\n</td><td class="upM" rowspan="2">\n<div align="center"><table border="7">\n<tr><td><b>Konzultační hodiny:</b>\n'
                     ' budova D, 204(Karlovo nám.)<!--<br />\n<!--po domluvě e-mailem: <a href="<?echo PAGE;?>page/mail">olga.majlingova&#064;fs.cvut.cz</a>-->\n</td></tr>\n</table>\n<p>\n<table border="0">\nVe zkouškovém období:\n'
                     '<tr><td>úterý</td> <td>26.5.</td><td>12:00-13:30</td></tr>\n<tr><td>čtvrtek</td><td>4.6.</td> <td>13:30-15:00</td></tr>\n<tr><td>úterý</td> <td>9.6.</td> <td>14:30-16:00</td></tr>\n<tr><td>čtvrtek</td><td>11.6.\n'
                     '</td><td>13:30-15:00</td></tr>\n<tr><td>čtvrtek</td><td>18.6.</td><td>13:30-15:00</td></tr>\n<tr><td>čtvrtek</td><td>2.7.</td> <td>13:30-15:00</td></tr>\n</table>\n</p>\n<p>\n<table><tr><td>\nRespektujte, prosím,\n'
                     ' uvedené termíny – cílem je\n</td></tr>\n<tr><td> udržet v kanceláři rozumné pracovní prostředí \n</td></tr>\n<tr><td>\na agendu související se zápisem známek \n</td></tr>\n<tr><td>\nomezit na konkrétní den a čas.\n'
                     '</td></tr></table>\n</p> \n</div>\n</td>\n<td>\n</td>\n</tr><tr>\n<td class="upR" rowspan="1" width="15%">\n</td>\n</tr>\n<tr><td colspan="3" class="lowtab">\n<a href="http://www.toplist.cz/stat/1075666"><script\n'
                     ' language="JavaScript" type="text/javascript">\n</a>\n</td></tr>\n</table>\n</body>\n</html>\n')
        cursor.execute("INSERT INTO transactions (id, method, uri, responseStatus, contentType, content, verificationStatusId, depth) VALUES (2, 'GET', \"http://olga.majling.eu/\", 200, \"text/html; charset=UTF-8\",?, 3, 1)", [response])
        con.commit()

        api = DBAPI(self.conf)
        tr = api.getTransaction()

        self.assertEqual(tr.getId(), 2)
        self.assertEqual(response.decode('utf-8'), tr.getContent())
        self.assertEqual(tr.getContentType(), "text/html")

        cursor.execute("SELECT verificationStatusId from transactions where id = 2")
        self.assertEqual(4, cursor.fetchone()[0])

        con.close()

    def testSetFinished(self):
        con = mdb.connect(self.conf.getDbname())
        cursor = con.cursor()
        cursor.execute("DELETE FROM transactions")
        response = ('<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n<title>408 Request Timeout</title>\n</head><body>\n<h1>Request Timeout</h1>\n<p>Server timeout waiting for the HTTP request from the client.</p>\n<hr>\n<address>Apache/2.4.10 (Debian) Server at olga.majling.eu Port 80</address>\n</body></html>')
        cursor.execute("INSERT INTO transactions (id, method, uri, responseStatus, contentType, content, verificationStatusId, depth) VALUES (1, 'GET', \"http://olga.majling.eu/Vyuka\", 200, \"text/html; charset=iso-8859-1\",?, 3, 1)", [response])
        con.commit()

        api = DBAPI(self.conf)
        tr = api.getTransaction()
        self.assertEqual(tr.getId(), 1)

        api.setFinished(tr.getId())

        cursor.execute("SELECT verificationStatusId from transactions where id = 1")
        self.assertEqual(5, cursor.fetchone()[0])

        con.close()

    def testSetLink(self):
        con = mdb.connect(self.conf.getDbname())
        cursor = con.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM link")
        cursor.execute("DELETE FROM finding")
        response = ('<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n<title>408 Request Timeout</title>\n</head><body>\n<h1>Request Timeout</h1>\n<p>Server timeout waiting for the HTTP request from the client.</p>\n<hr>\n<address>Apache/2.4.10 (Debian) Server at olga.majling.eu Port 80</address>\n</body></html>')
        cursor.execute("INSERT INTO transactions (id, method, uri, responseStatus, contentType, content, verificationStatusId, depth) VALUES (1, 'GET', \"http://olga.majling.eu/Vyuka\", 200, \"text/html; charset=iso-8859-1\",?, 3, 1)", [response])
        con.commit()

        api = DBAPI(self.conf)
        tr = api.getTransaction()
        self.assertEqual(tr.getId(), 1)

        api.setLink(tr.getId(), "http://olga.majling.eu/")

        cursor.execute("SELECT id FROM finding WHERE responseId = "+str(tr.getId()))
        findingId = cursor.fetchone()[0]
        cursor.execute("SELECT toUri, processed FROM link where findingId = "+str(findingId))
        row = cursor.fetchone()
        self.assertEqual("http://olga.majling.eu/", row[0])
        self.assertEqual(u'false', row[1])

if __name__ == '__main__':
    unittest.main()
