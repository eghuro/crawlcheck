# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external YAML file.
"""
import yaml
from pluginDBAPI import DBAPIconfiguration
from acceptor import Acceptor, RegexAcceptor
import logging
import sys
import re


class ConfigurationError(Exception):
    def __init__(self, msg):
        self.msg = msg


class EPR(object):
    def __init__(self, url, method='GET', data=dict()):
        self.url = url
        self.method = method
        self.data = data


class ConfigLoader(object):
    """ ConfigLoader loads configuration from file.
        Configuration is loaded through load()
        Later, DB configuration, URI and Content-Type acceptors can be
        retrieved through getters.
    """

    __VERSION = 1.05
    __METHODS = ['GET', 'POST']

    def __init__(self):
        self.__dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriRegexAcceptor = None
        self.entryPoints = []
        self.filters = []
        self.postprocess = []
        self.loaded = False
        self.properties = dict()
        self.payloads = dict()
        self.cookieFriendlyRegexes = set()
        self.customCookies = dict()
        self.__log = logging.getLogger(__name__)

        # defaults
        self.properties["pluginDir"] = "plugin"
        self.properties["agent"] = "Crawlcheck/"+str(ConfigLoader.__VERSION)
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
            self.__log.error("Configuration file error: " + e)

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
        elif str(root['version']) == str(ConfigLoader.__VERSION):
            version_check = True
        else:
            self.__log.error("Configuration version doesn't match (got " +
                             str(root['version']) + ", expected: " +
                             str(ConfigLoader.__VERSION) + ")")
        return version_check

    def __get_data(self, ep):
        data = dict()
        if 'data' in ep:
            for it in ep['data']:
                for k in it.keys():
                    data[k] = it[k]
        return data

    def __get_method(self, ep):
        method = 'GET'
        if 'method' in ep:
            if ep['method'].upper() in ConfigLoader.__METHODS:
                method = ep['method'].upper()
        return method

    def __set_entry_points(self, root):
        if 'entryPoints' not in root:
            self.__log.warning("Entry points should be specified")
        elif not root['entryPoints']:
            self.__log.warning("At least one entry point should be specified")
        else:
            epSet = root['entryPoints']
            for ep in epSet:
                self.__parse_entry_point(ep)

    def __parse_entry_point(self, ep):
        if type(ep) is str:
            self.entryPoints.append(EPR(ep))
        elif type(ep) is dict:
            data = self.__get_data(ep)
            method = self.__get_method(ep)
            if 'url' not in ep:
                raise ConfigurationException("url not present in entryPoint")
            self.entryPoints.append(EPR(ep['url'], method, data))

    def __set_plugins(self, root, tag, lst):
        if tag in root:
            for p in root[tag]:
                lst.append(p)
        return lst

    def __set_payloads(self, root):
        if 'payload' in root:
            for p in root['payload']:
                self.__parse_payload(p)

    def __parse_payload(self, p):
        if 'url' not in p:
            raise ConfigurationException("url not present in payload")
        if 'method' not in p:
            raise ConfigurationException("method not present in payload")
        if p['method'].upper() not in ConfigLoader.__METHODS:
            raise ConfigurationException("Invalid method: "+p['method'])
        if 'data' not in p:
            raise ConfigurationException("data not present in payload")

        self.payloads[(p['url'], p['method'].upper())] = p['data']

    def __set_cookies(self, root, u, us):
        # Go through urls again, grab cookie friendly prefixes
        if us in root:
            for url in root[us]:
                if ('cookie' in url) and (u in url):
                    self.__parse_cookie(url)
                # else: no cookie record or wrong url record -> raised earlier

    def __parse_cookie(self, url):
        # can be cookie: True/False parameter or structure
        if type(url['cookie']) is not bool:
            # structure
            if url['cookie']['reply']:
                reg = re.compile(url[u])
                self.cookieFriendlyRegexes.add(reg)
                if 'custom' in url['cookie']:
                    self.customCookies[reg] = url['cookie']['custom']
                    # self.customCookies[regex] = dict(key:value of cookies)
                # else: no cookies to send
            # else: forbidden to reply cookies and also send custom ones
        elif url['cookie']:  # cookie: True/False parameter
            self.cookieFriendlyRegexes.add(re.compile(url[u]))
        else:
            raise ConfigurationError("Wrong format of cookie record for " +
                                     url[u])

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

        # TODO: self.__set_cookies(root, u, us)

        # Grab lists
        self.__set_entry_points(root)
        self.filters = self.__set_plugins(root, 'filters', self.filters)
        self.postprocess = self.__set_plugins(root, 'postprocess',
                                              self.postprocess)
        self.__set_payloads(root)

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
            tags = root[tags_string]
            if tags:
                self.__run_tags(tags, description, acceptor, tag_string)
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
        if self.loaded:
            return Configuration(self.__dbconf, self.typeAcceptor,
                                 self.uriRegexAcceptor, self.entryPoints,
                                 self.properties, self.payloads,
                                 self.cookieFriendlyRegexes,
                                 self.customCookies, self.postprocess)
        else:
            return None

    def get_allowed_filters(self):
        if self.loaded:
            return self.filters
        else:
            return None


class Configuration(object):
    def __init__(self, db, ta, ra, ep, properties, pl, cfr, cc, pp):
        self.properties = properties
        self.dbconf = db
        self.dbconf.setLimit(self.getProperty("dbCacheLimit"))
        self.type_acceptor = ta
        self.regex_acceptor = ra
        self.entry_points = ep
        self.payloads = pl
        self.cookies = cfr
        # cookie friendly regexes -> eg. on these regexes we send cookies back
        self.custom_cookies = cc
        self.postprocess = pp

    def getProperty(self, key, default=None):
        if key in self.properties:
            return self.properties[key]
        else:
            return default
