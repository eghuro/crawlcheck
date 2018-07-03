# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external YAML file.
"""
from ruamel import yaml
from database import DatabaseConfiguration
from acceptor import Acceptor, RegexAcceptor
from common import ConfigurationError
import logging
import sys
import re


class EntryPointRecord(object):
    def __init__(self, url, method='GET', data=dict()):
        self.url = url
        self.method = method
        self.data = data


class ConfigLoader(object):
    """ ConfigLoader loads configuration from file.
        Configuration is loaded through load()
        When loaded, configuration object can be retrieved through
        get_configuration().
    """

    __CONFIG_VERSION = 1.05
    __APP_VERSION = 1.01

    def __init__(self):
        self.__dbconf = DatabaseConfiguration()
        self.typeAcceptor = None
        self.uriRegexAcceptor = None
        self.entryPoints = []
        self.filters = []
        self.postprocess = []
        self.loaded = False
        self.properties = dict()
        self.__log = logging.getLogger(__name__)

        # defaults
        self.properties["pluginDir"] = "plugin"
        self.properties["agent"] = "Crawlcheck/"+str(ConfigLoader.__APP_VERSION)
        self.properties["maxDepth"] = 0
        self.properties["timeout"] = 1
        self.properties["maxVolume"] = sys.maxsize
        self.properties["dbCacheLimit"] = sys.maxsize
        self.properties["verifyHttps"] = False
        self.properties["maxAttempts"] = 3
        self.properties["tmpPrefix"] = "Crawlcheck"
        self.properties["tmpSuffix"] = "content"

    def load(self, fname):
        """Loads configuration from YAML file.
        """
        cfile = open(fname)
        try:
            root = yaml.safe_load(cfile)

            db_check = self.__db_check(root)
            version_check = self.__version_check(root)
            if db_check and version_check:
                self.loaded = self.__set_up(root)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            self.__log.error("Configuration file error: " + str(e))

        cfile.close()

    def __db_check(self, root):
        if 'database' not in root:
            self.__log.error("Database not specified")
            return False
        else:
            return True

    def __version_check(self, root):
        version_check = False
        if 'version' not in root:
            self.__log.error("Version not specified")
        elif str(root['version']) == str(ConfigLoader.__CONFIG_VERSION):
            version_check = True
        else:
            self.__log.error("Configuration version doesn't match (got " +
                             str(root['version']) + ", expected: " +
                             str(ConfigLoader.__CONFIG_VERSION) + ")")
        return version_check

    def __set_entry_points(self, root):
        if 'entryPoints' not in root:
            self.__log.warning("Entry points should be specified")
        elif not root['entryPoints']:
            self.__log.warning("At least one entry point should be specified")
        else:
            epSet = root['entryPoints']
            for ep in epSet:
                self.entryPoints.append(EntryPointRecord(ep))

    def __set_plugins(self, root, tag, lst):
        if tag in root:
            for p in root[tag]:
                lst.append(p)
        return lst

    def __set_up(self, root):
        # Database is mandatory
        self.__dbconf.setDbname(root['database'])

        # Grab rules first
        cts = 'content-types'
        ct = 'content-type'
        ct_dsc = 'Content type'

        try:
            self.typeAcceptor = self.__get_acceptor(cts, ct, ct_dsc, root)
            self.uriRegexAcceptor = self.__create_uri_regex_acceptor(root)
        except ConfigurationError as e:
            self.__log.error(e.msg)
            return False

        # Grab lists
        self.__set_entry_points(root)

        if 'filters' not in root or not root['filters']:
            self.properties['all_filters'] = False
            self.filters = []
        else:
            if type(root['filters']) is bool:
                self.properties['all_filters'] = root['filters']
                self.filters = []
            else:
                self.properties['all_filters'] = False
                self.filters = self.__set_plugins(root, 'filters', self.filters)

        if 'postprocess' not in root or not root['postprocess']:
            self.properties['all_postprocess'] = False
            self.postprocess = []
        else:
            if type(root['postprocess']) is bool:
                self.properties['all_postprocess'] = root['postprocess']
                self.postprocess = []
            else:
                self.properties['all_postprocess'] = False
            self.postprocess = self.__set_plugins(root, 'postprocess',
                                                  self.postprocess)

        # Grab properties
        used_keys = set(['database', cts, 'regexes', 'version', 'entryPoints',
                         'filters', 'postprocess'])
        doc_keys = set(root.keys())
        for key in (doc_keys - used_keys):
            self.properties[key] = root[key]

        return True

    def __get_acceptor(self, tags_string, tag_string, description, root):
        acceptor = Acceptor()
        if tags_string in root:
            acceptor.empty = False
            tags = root[tags_string]
            if tags:
                self.__run_tags(tags, description, acceptor, tag_string)
        else:
            acceptor.empty = True
        return acceptor

    def __run_tags(self, tags, description, acceptor, tag_string):
        for tag in tags:
            if tag_string not in tag:
                raise ConfigurationError(description+" not specified")
            if 'plugins' in tag:
                ConfigLoader.__set_plugin_accept_tag_value(tag, tag_string,
                                                           acceptor)
                acceptor.setDefaultAcceptValue(tag[tag_string], True)
            else:
                self.__log.info("Forbidden: "+tag[tag_string])
                acceptor.setDefaultAcceptValue(tag[tag_string], False)

    def __create_uri_regex_acceptor(self, root):
        acceptor = RegexAcceptor()
        if 'regexes' in root:
            for regex in root['regexes']:
                self.__parse_regex(regex, acceptor)
        return acceptor

    def __parse_regex(self, regex, acceptor):
        if 'regex' not in regex:
            raise ConfigurationError("Regex not specified")
        if 'plugins' in regex:
            if regex['plugins'] is not None:
                for plugin in regex['plugins']:
                    acceptor.setRegex(regex['regex'], plugin)
            else:
                acceptor.setRegex(regex['regex'], None)

    @staticmethod
    def __set_plugin_accept_tag_value(tag, tag_string, acceptor):
        if tag['plugins']:
            for plugin in tag['plugins']:
                acceptor.setPluginAcceptValue(plugin, tag[tag_string], True)

    def get_configuration(self):
        """ Get the configuration object. """
        if self.loaded:
            return Configuration(self.__dbconf, self.typeAcceptor,
                                 self.uriRegexAcceptor, self.entryPoints,
                                 self.properties, self.postprocess)
        else:
            return None

    def get_allowed_filters(self):
        if self.loaded:
            return self.filters
        else:
            return None


class Configuration(object):
    def __init__(self, db, ta, ra, ep, properties, pp):
        self.properties = properties
        self.dbconf = db
        self.dbconf.setLimit(self.getProperty("dbCacheLimit"))
        self.type_acceptor = ta
        self.regex_acceptor = ra
        self.entry_points = ep
        self.postprocess = pp

    def getProperty(self, key, default=None):
        """ Get a value for a custom property.
        Default value is returned if the property is not specified.
        """

        if key in self.properties:
            if default is not None:
                if isinstance(self.properties[key], type(default)):
                    return self.properties[key]
                else:
                    return default
            return self.properties[key]
        else:
            return default
