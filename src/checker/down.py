import requests
import sqlite3 as mdb
from pluginDBAPI import Connector


class Scraper(object):
    def __init__(self, conf):
        self.con = Connector(conf)

    def scrapOne(self, uri):
        """ Download one page and insert it into transaction.
        """
        if not self.gotLink(uri):
            r = requests.get(uri)

            print("Adding entry point: "+uri)

            query = ('INSERT INTO transactions (uri, method, responseStatus, '
                     'contentType, origin, verificationStatusId, depth, '
                     'content) VALUES (?,\'GET\', ' + str(r.status_code) + ','
                     ' "' + r.headers['Content-Type'] + '", \'CLIENT\', 3, 1,'
                     ' ?)')

            self.con.get_cursor().execute(query, [uri, r.text])
            self.con.commit()

    def scrap(self, urilist):
        """ Download a list of pages and insert them into database.
        """
        for uri in urilist:
            print(uri)
        for uri in urilist:
            self.scrapOne(uri)

    def gotLink(self, toUri):
        try:
            query = ('SELECT count(id) FROM transactions WHERE method = '
                     '\'GET\' and uri = ?')
            self.con.get_cursor().execute(query, [toUri])
            row = self.con.get_cursor().fetchone()
            if row is not None:
                if row[0] is not None:
                    return row[0] != 0
            return False
        except mdb.Error as e:
            self.con.rollback()
            print("Error %s", (e.args[0]))
            return False
