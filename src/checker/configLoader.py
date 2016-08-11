# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external YAML file.
"""
import yaml
from pluginDBAPI import DBAPIconfiguration
from acceptor import Acceptor

class ConfigurationError(Exception):
    def __init__(self, msg):
        self.msg = msg

class ConfigLoader(object):
    """ ConfigLoader loads configuration from file.
        Configuration is loaded through load()
        Later, DB configuration, URI and Content-Type acceptors can be
        retrieved through getters.
    """

    _VERSION = 1.01

    def __init__(self):
        self.__dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriAcceptor = None
        self.entryPoints = []
        self.maxDepth = 0
        self.loaded = False
        self.agent = "Crawlcheck/"+_VERSION
        self.uriMap = Dict()

    def load(self, fname):
        """Loads configuration from YAML file.
        """
        cfile = open(fname)
        root = yaml.safe_load(cfile)

        db_check = ConfigLoader.__db_check(root)
        version_check = ConfigLoader.__version_check(root)
        if db_check and version_check:
            self.loaded = self.__set_up(root)
        
        cfile.close()

    @staticmethod
    def __db_check(root):
        if 'database' not in root:
            print("Database not specified")
            return False
        else:
            return True

    @staticmethod
    def __version_check(root):
        version_check = False
        if 'version' not in root:
            print("Version not specified")
        elif root['version'] == ConfigLoader._VERSION:
            version_check = True
        else:
            print("Configuration version doesn't match")
        return version_check

    def __set_max_depth(self, root):
        if 'maxDepth' in root:
            if root['maxDepth'] >= 0:
                self.maxDepth = root['maxDepth']
            else:
                print("Max depth must be zero or positive! Setting to 0.")
    
    def __set_entry_points(self, root):
        if 'entryPoints' not in root:
            print("Entry points should be specified")
        elif not root['entryPoints']:
            print("At least one entry point should be specified")
        else:
            epSet = root['entryPoints']
            for ep in epSet:
                self.entryPoints.append(ep)

    def __set_user_agent(self, root):
        if 'agent' in root:
            self.agent = root['agent']
 
    def __set_up(self, root):
        self.__dbconf.setDbname(root['database'])

        self.__set_max_depth(root)
        self.__set_entry_points(root)
        self.__set_user_agent(root)

        cts = 'content-types'
        ct = 'content-type'
        ct_dsc = 'Content type'

        us = 'urls'
        u = 'url'
        u_dsc = 'URL'

        try:
            uriPlugins = Dict()
            pluginTypes = Dict()
            self.typeAcceptor = ConfigLoader.__get_acceptor(cts, ct, ct_dsc, root, None, pluginTypes)
            self.uriAcceptor = ConfigLoader.__get_acceptor(us, u, u_dsc, root, uriPlugins, None)

            #create mapping of accepted content types for URI
            uris = self.uriAcceptor.getValues()
            for uri in uris:
                for plugin in self.uriPlugin[uri]:
                    #put list of types for plugin into a dict for uri; merge lists together
                    if not self.uriMap[uri]:
                        self.uriMap[uri] = []
                    self.uriMap[uri] += pluginTypes[plugin]
        except ConfigurationError as e:
            print(e.msg)
            return False
        return True

    @staticmethod
    def __get_acceptor(tags_string, tag_string, description, root, record, drocer):
        acceptor = Acceptor(False)
        if tags_string in root:
            tags = root[tags_string]
            if tags:
                ConfigLoader.__run_tags(tags, description, acceptor, tag_string, record, drocer)
        return acceptor

    @staticmethod
    def __run_tags(tags, description, acceptor, tag_string, record, drocer):
        for tag in tags:
            if tag_string not in tag:
                raise ConfigurationError(description+" not specified")
            if 'plugins' in tag:
                ConfigLoader._set_plugin_accept_tag_value(tag, tag_string, acceptor, record, drocer)
            else:
                print("Forbid "+tag[tag_string])
                acceptor.setDefaultAcceptValue(tag[tag_string], False)

    @staticmethod
    def __set_plugin_accept_tag_value(tag, tag_string, acceptor, record, drocer):
        if tag['plugins']:
            for plugin in tag['plugins']:
                acceptor.setPluginAcceptValue(plugin, tag[tag_string], True)

                #TODO: refactor hard
                if record is not None:
                    if not record[tag[tag_string]]:
                        record[tag[tag_string]] = [plugin]
                    else:
                        record[tag[tag_string]].append(plugin)
                        #zde operuji s predpokladem, ze v seznamu adres bude kazdy plugin nejvyse jednou
                else: #predpoklad, ze mame pouze 2 acceptory (uri a type); ten se projevuje i v parametrech (record, drocer)
                    if not drocer[plugin]:
                        drocer[plugin] = [tag[tag_string]]
                    elif tag[tag_string] not in drocer[plugin]:
                        drocer[plugin].append(tag[tag_string])

    def get_dbconf(self):
        """ Retrieve DB configuration.
        """
        if self.loaded:
            return self._dbconf
        else:
            return None

    def get_type_acceptor(self):
        """ Retrieve Acceptor instance for Content-Type.
        """
        if self.loaded:
            return self.typeAcceptor
        else:
            return None

    def get_uri_acceptor(self):
        """ Retrieve Acceptor instance for URI.
        """
        if self.loaded:
            return self.uriAcceptor
        else:
            return None

    def get_entry_points(self):
        """ Retrieve list of URIs for initial requests.
        """
        if self.loaded:
            return self.entryPoints
        else:
            return None

    def get_max_depth(self):
        """ Get maximum depth for crawling (0 for no limit)
        """
        if self.loaded:
            return self.maxDepth
        else:
            return None

    def get_user_agent(self):
        if self.loaded:
            return self.agent
        else:
            return None

    def get_uri_map(self):
        if self.loaded:
            return self.uriMap
        else:
            return None
