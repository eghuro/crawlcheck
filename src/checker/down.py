import requests
from pluginDBAPI import DBAPI


class Scraper(object):
    def __init__(self, conf):
        self.__api = DBAPI(conf)

    def scrap_one(self, uri):
        """ Download one page and insert it into transaction.
        """
        if not self.__api.gotLink(uri):
            r = requests.get(uri)

            print("Adding entry point: "+uri)

            #set request using DBAPI
            self.__api.setRequest(uri, str(r.status_code), 
                                  r.headers["Content-Type"], r.text)

    def scrap(self, urilist):
        """ Download a list of pages and insert them into database.
        """
        for uri in urilist:
            print(uri)
        for uri in urilist:
            self.scrap_one(uri)
