# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external YAML file.
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
        self.maxDepth = 0

    def load(self, fname):
        """Loads configuration from YAML file.
        """
        cfile = open(fname)
        root = yaml.safe_load(cfile)

        if 'version' not in root:
           print("Version not specified")
        elif 'database' not in root:
           print("Database not specified")
        elif root['version'] == self.version:
           self.set_up(root)
        else:
           print("Configuration version doesn't match")
        cfile.close()

    def set_up(self, root):
       self.dbconf.setDbname(root['database'])

       if 'maxDepth' in root:
         self.maxDepth = root['maxDepth']

       if 'entryPoints' not in root:
         print("Entry points should be specified")
       elif not root['entryPoints']:
         print("At least one entry point should be specified")
       else:
         epSet = root['entryPoints']
         for ep in epSet:
           self.entryPoints.append(ep)


         self.typeAcceptor = ConfigLoader.getAcceptor('content-types', 'content-type', 'Content type', root)
         self.uriAcceptor = ConfigLoader.getAcceptor('urls', 'url', 'URL', root)

    @staticmethod
    def getAcceptor(tags_string, tag_string, description, root):
        acceptor = Acceptor(False)
        if tags_string in root:
            tags = root[tags_string]
            if tags:
                for tag in tags:
                    if tag_string not in tag:
                        print(description+" not specified")
                        break
                    if 'plugins' in tag:
                        if tag['plugins']:
                            for plugin in tag['plugins']:
                                acceptor.setPluginAcceptValue(plugin, tag[tag_string], True)
                    else:
                        print("Forbid "+tag[tag_string])
                        acceptor.setDefaultAcceptValue(tag[tag_string], False)
        return acceptor

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

    def getMaxDepth(self):
         """ Get maximum depth for crawling (0 for no limit)
         """
         return self.maxDepth

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
