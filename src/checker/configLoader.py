# -*- coding: utf-8 -*-
"""Configuration Loader loads configuration from external YAML file.
"""
import yaml
from pluginDBAPI import DBAPIconfiguration
from acceptor import Acceptor, RegexAcceptor
import logging
import sys

class ConfigurationError(Exception):
    def __init__(self, msg):
        self.msg = msg

class EPR(object):
    def __init__(self, url, method='GET', data = dict()):
        self.url = url
        self.method = method
        self.data = data

class ConfigLoader(object):
    """ ConfigLoader loads configuration from file.
        Configuration is loaded through load()
        Later, DB configuration, URI and Content-Type acceptors can be
        retrieved through getters.
    """

    __VERSION = 1.03
    __METHODS = ['GET', 'POST']

    def __init__(self):
        self.__dbconf = DBAPIconfiguration()
        self.typeAcceptor = None
        self.uriAcceptor = None
        self.uriRegexAcceptor = None
        self.entryPoints = []
        self.filters = []
        self.loaded = False
        self.uriMap = None
        self.suffixUriMap = None
        self.properties = dict()
        self.payloads = dict()
        self.cookieFriendlyPrefixes = set()
        self.customCookies = dict()
        self.__log = logging.getLogger(__name__)

        #defaults
        self.properties["pluginDir"] = "plugin"
        self.properties["agent"] = "Crawlcheck/"+str(ConfigLoader.__VERSION)
        self.properties["maxDepth"] = 0
        self.properties["timeout"] = 1
        self.properties["maxVolume"] = sys.maxsize
        self.properties["dbCacheLimit"] = sys.maxsize
        self.properties["verifyHttps"] = False

    def load(self, fname):
        """Loads configuration from YAML file.
        """
        cfile = open(fname)
        try:
            root = yaml.safe_load(cfile)

            db_check = ConfigLoader.__db_check(root)
            version_check = ConfigLoader.__version_check(root)
            if db_check and version_check:
                self.loaded = self.__set_up(root)
        except yaml.scanner.ScannerError as e:
            self.__log.error("Configuration file error: " + e)

        cfile.close()

    @staticmethod
    def __db_check(root):
        if 'database' not in root:
            self.__log.error("Database not specified")
            return False
        else:
            return True

    @staticmethod
    def __version_check(root):
        version_check = False
        if 'version' not in root:
            self.__log.error("Version not specified")
        elif str(root['version']) == str(ConfigLoader.__VERSION):
            version_check = True
        else:
            self.__log.error("Configuration version doesn't match (got "+str(root['version'])+", expected: "+str(ConfigLoader.__VERSION)+")")
        return version_check

    ###

    def __set_entry_points(self, root):
        if 'entryPoints' not in root:
            self.__log.warning("Entry points should be specified")
        elif not root['entryPoints']:
            self.__log.warning("At least one entry point should be specified")
        else:
            epSet = root['entryPoints']
            for ep in epSet:
                if type(ep) is str:
                    self.entryPoints.append(EPR(ep))
                elif type(ep) is dict:
                    data = dict()
                    if 'data' in ep:
                        for it in ep['data']:
                            for k in it.keys():
                                data[k] = it[k]
                    method = 'GET'
                    if 'method' in ep:
                        if ep['method'].upper() in ConfigLoader.__METHODS:
                            method = ep['method'].upper()
                    if 'url' not in ep:
                        raise ConfigurationException("url not present in entryPoint")
                    self.entryPoints.append(EPR(ep['url'], method, data))

    def __set_filters(self, root):
        if 'filters' in root:
            for f in root['filters']:
                self.filters.append(f)

    def __set_payloads(self, root):
        if 'payload' in root:
            for p in root['payload']:
                if 'url' not in p:
                    raise ConfigurationException("url not present in payload")
                if 'method' not in p:
                    raise ConfigurationException("method not present in payload")
                if p['method'].upper() not in ConfigLoader.__METHODS:
                    raise ConfigurationException("Invalid method: "+p['method'])
                if 'data' not in p:
                    raise ConfigurationException("data not present in payload")

                self.payloads[ (p['url'], p['method'].upper()) ] = p['data']

    def __set_cookies(self, root, u, us):
        #Go through urls again, grab cookie friendly prefixes
        if us in root:
          for url in root[us]:
            if ('cookie' in url) and (u in url):
                # can be cookie: True/False parameter or structure
                if type(url['cookie']) is not bool:
                    #structure
                    if url['cookie']['reply']:
                        self.cookieFriendlyPrefixes.add(url[u])
                        if 'custom' in url['cookie']:
                            self.customCookies[url[u]] = url['cookie']['custom']
                            #self.customCookies[prefix] = dict(key:value of cookies)
                        #else: no cookies to send
                    #else: forbidden to reply cookies and also send custom ones
                elif url['cookie']: #cookie: True/False parameter
                    self.cookieFriendlyPrefixes.add(url[u])
                else:
                    raise ConfigurationError("Wrong format of cookie record for "+url[u])
            #else: no cookie record or wrong url record -> raised earlier
 
    def __set_up(self, root):
        #Database is mandatory
        self.__dbconf.setDbname(root['database'])

        #Grab rules first
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
            suffixUriPlugins = dict()
            pluginTypes = dict()
            self.typeAcceptor = self.__get_acceptor(cts, ct, ct_dsc, root, None, pluginTypes)
            self.uriAcceptor = self.__get_acceptor(us, u, u_dsc, root, uriPlugins, None)
            self.suffixAcceptor = self.__get_acceptor(sus, su, su_dsc, root, suffixUriPlugins, None)
            self.suffixAcceptor.reverseValues()
            suffixUriPlugins = ConfigLoader.reverse_dict_keys(suffixUriPlugins)
            self.uriMap = self.create_uri_plugin_map(uriPlugins, pluginTypes, self.uriAcceptor)
            self.suffixMap = self.create_uri_plugin_map(suffixUriPlugins, pluginTypes, self.suffixAcceptor)
            self.uriRegexAcceptor = self.__create_uri_regex_acceptor(root)
        except ConfigurationError as e:
            self.__log.error(e.msg)
            return False

        self.__set_cookies(root, u, us)

        #Grab lists
        self.__set_entry_points(root)
        self.__set_filters(root)
        self.__set_payloads(root)

        #Grab properties
        used_keys = set(['database', cts, us, sus, 'version', 'entryPoints', 'filters'])
        doc_keys = set(root.keys())
        for key in (doc_keys - used_keys):
            self.properties[key] = root[key]
        
        return True

    def __get_acceptor(self, tags_string, tag_string, description, root, record, drocer):
        acceptor = Acceptor()
        if tags_string in root:
            tags = root[tags_string]
            if tags:
                self.__run_tags(tags, description, acceptor, tag_string, record, drocer)
        return acceptor

    def __run_tags(self, tags, description, acceptor, tag_string, record, drocer):
        for tag in tags:
            if tag_string not in tag:
                raise ConfigurationError(description+" not specified")
            if 'plugins' in tag:
                ConfigLoader.__set_plugin_accept_tag_value(tag, tag_string, acceptor, record, drocer)
                acceptor.setDefaultAcceptValue(tag[tag_string], True)
            else:
                self.__log.info("Forbidden: "+tag[tag_string])
                acceptor.setDefaultAcceptValue(tag[tag_string], False)

    def __create_uri_regex_acceptor(self, root):
       acceptor = RegexAcceptor()
       if 'regexes' in root:
           regexes = root['regexes']
           if regexes:
               for regex in regexes:
                   if 'regex' not in regex:
                       raise ConfigurationError("Regex not specified")
                   if 'plugins' in regex:
                       for plugin in regex['plugins']:
                           acceptor.setRegex(regex['regex'], plugin)
       return acceptor


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

    def create_uri_plugin_map(self, uriPlugin, pluginTypes, uriAcceptor):
        uriMap = dict()
        #create mapping of accepted content types for URI:

        for uri in uriAcceptor.getPositiveValues(): #accepted prefixes
            if uri in uriPlugin: #any plugin accepting this prefix? (careful!!)
                for plugin in uriPlugin[uri]:
                    if not plugin in pluginTypes:
                        self.__log.warn(plugin+" doesn't have any content type associated")
                    else:
                        #put list of types for plugin into a dict for uri; join sets together
                        if uri not in uriMap:
                            uriMap[uri] = set()
                        uriMap[uri].update(pluginTypes[plugin])
            else:
                self.__log.debug("Uri not in uriPlugin: "+uri)
        return uriMap

    def get_configuration(self):
        if self.loaded:
            return Configuration(self.__dbconf, self.typeAcceptor, self.uriAcceptor, self.suffixAcceptor, self.uriRegexAcceptor, self.entryPoints, self.uriMap, self.suffixUriMap, self.properties, self.payloads, self.cookieFriendlyPrefixes, self.customCookies)
        else:
            return None

    def get_allowed_filters(self):
        if self.loaded:
            return self.filters
        else:
            return None

    @staticmethod
    def reverse_dict_keys(sufdict):
        revdict = dict()
        for key in sufdict.keys():
            revkey = key[::-1]
            revdict[revkey] = sufdict[key]
        return revdict

class Configuration(object):
    def __init__(self, db, ta, ua, sa, ra, ep, um, su, properties, pl, cfp, cc):
        self.properties = properties
        self.dbconf = db
        self.dbconf.setLimit(self.getProperty("dbCacheLimit"))
        self.type_acceptor = ta
        self.uri_acceptor = ua
        self.suffix_acceptor = sa
        self.regex_acceptor = ra
        self.entry_points = ep
        self.uri_map = um
        self.suffix_uri_map = su
        self.payloads = pl
        self.cookies = cfp #cookie friendly prefixes -> eg. on these prefixes we send cookies back
        self.custom_cookies = cc

    def getProperty(self, key):
        if key in self.properties:
            return self.properties[key]
        else:
            return None
