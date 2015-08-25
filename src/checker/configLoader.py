import xml.etree.ElementTree as etree
from pluginDBAPI import DBAPIconfiguration
from acceptor import Acceptor

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

            plugins = root.find('plugins')

            self.getResolutions(plugins)

            pluginSet = plugins.findall('plugin')
            for plugin in pluginSet:
                pluginId = plugin.attrib['id']
                self.getPluginResolutions(pluginId, plugin, self.uriAcceptor, self.typeAcceptor)
        else:
            print "Configuration version doesn't match"

    def getDbconf(self):
        return self.dbconf

    def getTypeAcceptor(self):
        return self.typeAcceptor

    def getUriAcceptor(self):
        return self.uriAcceptor

    def getDefaults(self, root, setKeyword, keyword):
        defaultSet = root.find(setKeyword)
        acceptor = Acceptor(defaultSet.attrib['default'] == 'True')

        defaultElements = defaultSet.findall(keyword)
        for element in defaultElements:
            acceptor.setDefaultAcceptValue(element.attrib['key'], element.attrib['accept'])

        return acceptor

    def getResolutions(self, root):
        defaults = root.find('resolutions') 
        self.uriAcceptor = self.getDefaults(defaults, 'uris', 'uri')
        self.typeAcceptor = self.getDefaults(defaults, 'contentTypes', 'contentType')

    def getPluginDefaults(self, pluginId, root, setKeyword, keyword, acceptor):
        defaultSet = root.find(setKeyword)
        acceptor.setPluginAcceptValueDefault(pluginId, defaultSet.attrib['default'] == 'True')

        defaultElements = defaultSet.findall(keyword)
        for element in defaultElements:
            acceptor.setPluginAcceptValue(pluginId, element.attrib['key'], element.attrib['accept'])

    def getPluginResolutions(self, pluginId, root, uriAcceptor, typeAcceptor):
        defaults = root.find('resolutions')
        self.getPluginDefaults(pluginId, defaults, 'uris', 'uri', uriAcceptor)
        self.getPluginDefaults(pluginId, defaults, 'contentTypes', 'contentType', typeAcceptor)
