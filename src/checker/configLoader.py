# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external XML file.
"""
import xml.etree.ElementTree as etree
from pluginDBAPI import DBAPIconfiguration
from acceptor import Acceptor


class ConfigLoader(object):
    """ ConfigLoader loads configuration from file.
        Configuration is loaded through load()
        Later, DB configuration, URI and Content-Type acceptors can be retrieved through getters.
    """
    def __init__(self):
        self.version = "0.01"
        self.dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriAcceptor = None
        self.entryPoints = []

    def load(self, fname):
        """Loads configuration from XML file.
        """
        tree = etree.parse(fname)
        root = tree.getroot()

        if root.attrib['version'] == self.version:
            dbAtts = root.find('db').attrib

            self.dbconf.setUri(dbAtts['uri'])
            self.dbconf.setPassword(dbAtts['pass'])
            self.dbconf.setDbname(dbAtts['dbname'])
            self.dbconf.setUser(dbAtts['user'])

            eps = root.find('entryPoints')
            epSet = eps.findall('entryPoint')
            for ep in epSet:
                self.entryPoints.append(ep.attrib['uri'])

            plugins = root.find('plugins')

            self.getResolutions(plugins)

            pluginSet = plugins.findall('plugin')
            for plugin in pluginSet:
                pluginId = plugin.attrib['id']
                self.getPluginResolutions(pluginId, plugin, self.uriAcceptor,
                                          self.typeAcceptor)
        else:
            print "Configuration version doesn't match"

    def getDbconf(self):
        """ Retrieve DB configuration.
        """
        return self.dbconf

    def getTypeAcceptor(self):
        """ Retrieve Acceptor instance for Content-Type.
        """
        return self.typeAcceptor

    def getUriAcceptor(self):
        """ Retrieve Acceptor instance for URI.
        """
        return self.uriAcceptor

    def getEntryPoints(self):
        """ Retrieve list of URIs for initial requests.
        """
        return self.entryPoints

    def getDefaults(self, root, setKeyword, keyword):
        defaultSet = root.find(setKeyword)
        if defaultSet is not None:
            acceptor = Acceptor(defaultSet.attrib['default'] == 'True')

            defaultElements = defaultSet.findall(keyword)
            if defaultElements is not None:
                for element in defaultElements:
                    acceptor.setDefaultAcceptValue(element.attrib['key'],
                                                   element.attrib['accept'] ==
                                                   'True')

                return acceptor
            else:
                return None

    def getResolutions(self, root):
        defaults = root.find('resolutions')
        if defaults is not None:
            self.uriAcceptor = self.getDefaults(defaults, 'uris', 'uri')
            self.typeAcceptor = self.getDefaults(defaults, 'contentTypes',
                                                 'contentType')

    def getPluginDefaults(self, pluginId, root, setKeyword, keyword, acceptor):
        defaultSet = root.find(setKeyword)
        if defaultSet is not None:
            acceptor.setPluginAcceptValueDefault(pluginId,
                                                 defaultSet.attrib['default'] ==
                                                 'True')

            defaultElements = defaultSet.findall(keyword)
            if defaultElements is not None:
                for element in defaultElements:
                    acceptor.setPluginAcceptValue(pluginId,
                                                  element.attrib['key'],
                                                  element.attrib['accept'] ==
                                                  'True')

    def getPluginResolutions(self, pluginId, root, uriAcceptor, typeAcceptor):
        defaults = root.find('resolutions')
        if defaults is not None:
            self.getPluginDefaults(pluginId, defaults, 'uris', 'uri', uriAcceptor)
            self.getPluginDefaults(pluginId, defaults, 'contentTypes',
                                   'contentType', typeAcceptor)
