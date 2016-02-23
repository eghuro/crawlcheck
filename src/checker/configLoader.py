# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external YAML file.
"""
import yaml
from pluginDBAPI import DBAPIconfiguration
from acceptor import Acceptor


class ConfigLoader(object):
    """ ConfigLoader loads configuration from file.
        Configuration is loaded through load()
        Later, DB configuration, URI and Content-Type acceptors can be
        retrieved through getters.
    """
    def __init__(self):
        self.version = 1.01
        self.dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriAcceptor = None
        self.entryPoints = []
        self.maxDepth = 0
        self.loaded = False

    def load(self, fname):
        """Loads configuration from YAML file.
        """
        cfile = open(fname)
        root = yaml.safe_load(cfile)

        db_check = self.db_check(root)
        version_check = self.version_check(root)
        if db_check and version_check:
            self.set_up(root)
            self.loaded = True
        
        cfile.close()

    def db_check(self, root):
        if 'database' not in root:
            print("Database not specified")
            return False
        else:
            return True

    def version_check(self, root):
        version_check = False
        if 'version' not in root:
            print("Version not specified")
        elif root['version'] == self.version:
            version_check = True
        else:
            print("Configuration version doesn't match")
        return version_check

    def set_max_depth(self, root):
        if 'maxDepth' in root:
            if root['maxDepth'] >= 0:
                self.maxDepth = root['maxDepth']
            else:
                print("Max depth must be zero or positive! Setting to 0.")
    
    def set_entry_points(self, root):
        if 'entryPoints' not in root:
            print("Entry points should be specified")
        elif not root['entryPoints']:
            print("At least one entry point should be specified")
        else:
            epSet = root['entryPoints']
            for ep in epSet:
                self.entryPoints.append(ep)
 
    def set_up(self, root):
        self.dbconf.setDbname(root['database'])

        self.set_max_depth(root)
        self.set_entry_points(root)

        cts = 'content-types'
        ct = 'content-type'
        ct_dsc = 'Content type'

        us = 'urls'
        u = 'url'
        u_dsc = 'URL'

        self.typeAcceptor = ConfigLoader.get_acceptor(cts, ct, ct_dsc, root)
        self.uriAcceptor = ConfigLoader.get_acceptor(us, u, u_dsc, root)

    @staticmethod
    def get_acceptor(tags_string, tag_string, description, root):
        acceptor = Acceptor(False)
        if tags_string in root:
            tags = root[tags_string]
            if tags:
                ConfigLoader.run_tags(tags, description, acceptor, tag_string)
        return acceptor

    @staticmethod
    def run_tags(tags, description, acceptor, tag_string):
        for tag in tags:
            if tag_string not in tag:
                print(description+" not specified")
                break
            if 'plugins' in tag:
                ConfigLoader.set_plugin_accept_tag_value(tag, tag_string, acceptor)
            else:
                print("Forbid "+tag[tag_string])
                acceptor.setDefaultAcceptValue(tag[tag_string], False)

    @staticmethod
    def set_plugin_accept_tag_value(tag, tag_string, acceptor):
        if tag['plugins']:
            for plugin in tag['plugins']:
                acceptor.setPluginAcceptValue(plugin, tag[tag_string], True)

    def getDbconf(self):
        """ Retrieve DB configuration.
        """
        if self.loaded:
            return self.dbconf
        else:
            return None

    def getTypeAcceptor(self):
        """ Retrieve Acceptor instance for Content-Type.
        """
        if self.loaded:
            return self.typeAcceptor
        else:
            return None

    def getUriAcceptor(self):
        """ Retrieve Acceptor instance for URI.
        """
        if self.loaded:
            return self.uriAcceptor
        else:
            return None

    def getEntryPoints(self):
        """ Retrieve list of URIs for initial requests.
        """
        if self.loaded:
            return self.entryPoints
        else:
            return None

    def getMaxDepth(self):
        """ Get maximum depth for crawling (0 for no limit)
        """
        if self.loaded:
            return self.maxDepth
        else:
            return None

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
            value = defaultSet.attrib['default'] == 'True'
            acceptor.setPluginAcceptValueDefault(pluginId, value)

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
            u = 'uri'
            us = 'uris'
            self.getPluginDefaults(pluginId, defaults, us, u, uriAcceptor)
            self.getPluginDefaults(pluginId, defaults, 'contentTypes',
                                   'contentType', typeAcceptor)
