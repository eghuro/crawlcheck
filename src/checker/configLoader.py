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

    __VERSION = 1.02

    def __init__(self):
        self.__dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriAcceptor = None
        self.entryPoints = []
        self.maxDepth = 0
        self.loaded = False
        self.agent = "Crawlcheck/"+str(ConfigLoader.__VERSION)
        self.uriMap = None
        self.suffixUriMap = None

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
        elif str(root['version']) == str(ConfigLoader.__VERSION):
            version_check = True
        else:
            print("Configuration version doesn't match (got "+str(root['version'])+", expected: "+str(ConfigLoader.__VERSION)+")")
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

        sus = 'suffixes'
        su = 'suffix'
        su_dsc = 'Suffix'

        try:
            uriPlugins = dict()
            sufixUriPlugins = dict()
            pluginTypes = dict()
            self.typeAcceptor = ConfigLoader.__get_acceptor(cts, ct, ct_dsc, root, None, pluginTypes)
            self.uriAcceptor = ConfigLoader.__get_acceptor(us, u, u_dsc, root, uriPlugins, None)
            self.suffixAcceptor = ConfigLoader.__get_acceptor(sus, su, su_dsc, root, suffixUriPlugins, None)
            self.suffixAcceptor.reverseValues()
            self.__revese_dict_values(suffixUriPlugins)
            self.uriMap = self.__create_uri_plugin_map(uriPlugins, pluginTypes)
            self.suffixMap = self.__create_uri_plugin_map(suffixUriPlugins, pluginTypes)
        except ConfigurationError as e:
            print(e.msg)
            return False
        return True

    @staticmethod
    def __get_acceptor(tags_string, tag_string, description, root, record, drocer):
        acceptor = Acceptor()
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
                ConfigLoader.__set_plugin_accept_tag_value(tag, tag_string, acceptor, record, drocer)
            else:
                print("Forbid "+tag[tag_string])
                acceptor.setDefaultAcceptValue(tag[tag_string], False)

    @staticmethod
    def __set_plugin_accept_tag_value(tag, tag_string, acceptor, record, drocer):
        if tag['plugins']:
            for plugin in tag['plugins']:
                acceptor.setPluginAcceptValue(plugin, tag[tag_string], True)

                #TODO: refactor hard #TODO: TESTME!!
                if record is not None:
                    if tag[tag_string] not in record:
                        record[tag[tag_string]] = set([plugin])
                    else:
                        record[tag[tag_string]].add(plugin)
                elif drocer is not None:
                    if plugin not in drocer:
                        drocer[plugin] = set([tag[tag_string]])
                    elif tag[tag_string] not in drocer[plugin]:
                        drocer[plugin].add(tag[tag_string])

    def __create_uri_plugin_map(self, uriPlugin, pluginTypes):
        uriMap = dict()
        #create mapping of accepted content types for URI
        for uri in self.uriAcceptor.getPositiveValues():
            if uri in uriPlugin:
                for plugin in uriPlugin[uri]:
                    #put list of types for plugin into a dict for uri; join sets together
                    if uri not in self.uriMap:
                        uriMap[uri] = set()
                    uriMap[uri].update(pluginTypes[plugin])
            else:
                print("Uri not in uriPlugin: "+uri)
        return uriMap

    def get_configuration(self):
        if self.loaded:
            return Configuration(self.__dbconf, self.typeAcceptor, self.uriAcceptor, self.suffixAcceptor, self.entryPoints, self.maxDepth, self.agent, self.uriMap, self.suffixUriMap)
        else:
            return None

    def __reverse_dict_values(self, sufdict):
        for key in sufdict.keys():
            lst = []
            for val in sufdict[key]:
                lst.append(val[::-1])
            sufdict[key]=lst

class Configuration(object):
    def __init__(self, db, ta, ua, sa, ep, md, ag, um, su):
        self.dbconf = db
        self.type_acceptor = ta
        self.uri_acceptor = ua
        self.suffix_acceptor = sa
        self.entry_points = ep
        self.max_depth = md
        self.user_agent = ag
        self.uri_map = um
        self.suffix_uri_map = su
