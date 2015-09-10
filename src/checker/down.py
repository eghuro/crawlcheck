import requests
import sqlite3 as mdb


class Scraper(object):
    def __init__(self, conf):
        self.con = mdb.connect(conf.getDbname())
        self.cursor = self.con.cursor()

    def __del__(self):
        if self.con:
            self.con.close()

    def scrapOne(self, uri):
        """ Download one page and insert it into transaction.
        """
        if not self.gotLink(uri):
           r = requests.get(uri)

           print "Adding entry point: "+uri

           self.cursor.execute("set names utf8;")

           query = ('INSERT INTO transactions (uri, method, responseStatus, contentType, origin, verificationStatusId, content) VALUES ('
                    '?,\'GET\', ' + str(r.status_code) + ', "' + r.headers['Content-Type'] +'", \'CLIENT\', 3, "%s")')
           self.cursor.execute(query, [uri, r.text.encode("utf-8").strip()[:65535]])
           self.con.commit()

    def scrap(self, urilist):
        """ Download a list of pages and insert them into database.
        """
        for uri in urilist:
           print uri
        for uri in urilist:
           self.scrapOne(uri)

    def gotLink(self, toUri):
        try:
           query = ('SELECT id FROM transactions WHERE method = \'GET\' and '
                    'uri = ?')
           self.cursor.execute(query, [toUri])
           return self.cursor.rowcount != 0
        except mdb.Error, e:
           if self.con:
              self.con.rollback()
           print "Error %s" % (e.args[0])
           return False
