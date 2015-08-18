import xml.etree.ElementTree as etree
from pluginDBAPI import DBAPIconfiguration

class ConfigLoader:
    def __init__(self):
        self.version = "0.00"
        self.dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriAcceptor = None

    def load(self, fname):
        tree = etree.parse(fname)
        root = tree.getroot()

        if root.attrib['version'] == self.version:
            dbAtts = root.find('db').attrib

            self.dbconf.setUri(dbAtts['uri'])
            self.dbconf.setPassword(dbAtts['pass'])
            self.dbconf.setDbname(dbAtts['dbname'])
            self.dbconf.setUser(dbAtts['user'])
        else:
            print "Configuration version doesn't match"

    def getDbconf(self):
        return self.dbconf

    def getTypeAcceptor(self):
        return self.typeAcceptor

    def getUriAcceptor(self):
        return self.uriAcceptor
