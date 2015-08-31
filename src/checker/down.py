import requests
import MySQLdb as mdb


class Scraper(object):
    def __init__(self, conf):
        self.con = mdb.connect(conf.getUri(), conf.getUser(),
                               conf.getPassword(), conf.getDbname())
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

           query = ('INSERT INTO transaction (uri, method, responseStatus, contentType, origin, verificationStatusId, content) VALUES ("'
                    ''+self.con.escape_string(uri)+'",\'GET\', ' + str(r.status_code) + ', "' + r.headers['Content-Type'] +'", \'CLIENT\', 3, "%s")')
           self.cursor.execute(query, [r.text.encode("utf-8").strip()[:65535]])
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
           query = ('SELECT id FROM transaction WHERE method = \'GET\' and '
                    'uri = "'+self.con.escape_string(toUri)+'"')
           self.cursor.execute(query)
           return self.cursor.rowcount != 0
        except mdb.Error, e:
           if self.con:
              self.con.rollback()
           print "Error %d: %s" % (e.args[0], e.args[1])
           return False
