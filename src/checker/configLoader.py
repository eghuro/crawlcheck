# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external XML file.
"""
import yaml
from pluginDBAPI import DBAPIconfiguration
from acceptor import Acceptor


class ConfigLoader(object):
    """ ConfigLoader loads configuration from file.
        Configuration is loaded through load()
        Later, DB configuration, URI and Content-Type acceptors can be retrieved through getters.
    """
    def __init__(self):
        self.version = 1.01
        self.dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriAcceptor = None
        self.entryPoints = []

    def load(self, fname):
        """Loads configuration from XML file.
        """
        cfile = open(fname)
        root = yaml.safe_load(cfile)

        if root['version'] == self.version:
           self.dbconf.setDbname(root['database'])

           epSet = root['entryPoints']
           for ep in epSet:
              self.entryPoints.append(ep)

           ctypes = root['content-types']
           self.typeAcceptor = Acceptor(False)
           for ctype in ctypes:
             for plugin in ctype['plugins']:
               self.typeAcceptor.setPluginAcceptValue(plugin, ctype['content-type'], True)

           urls = root['urls']
           self.uriAcceptor = Acceptor(False)
           for url in urls:
             for plugin in url['plugins']:
               self.uriAcceptor.setPluginAcceptValue(plugin, url['url'], True)
        else:
           print "Configuration version doesn't match"
        cfile.close()

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
