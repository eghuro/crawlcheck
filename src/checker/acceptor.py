# -*- coding: utf-8 -*-
"""Decision if a transaction is checked by a plugin.

Acceptor module contains business rules to decide if a transaction will be
checked by a plugin.
"""

from common import ConfigurationError
import marisa_trie
import re
from enum import Enum
import sre_constants


class Resolution(Enum):
    """Resolution enum helps apply a three state logic in Acceptor.
    Posible resolutions are yes, no or none.
    """

    yes = 1
    no = 2
    none = 3


class RegexAcceptor(object):
    def __init__(self):
        self.__regexes = dict()

    def canTouch(self, value):
        for plugin in self.__regexes.keys():
            for regex in self.__regexes[plugin]:
                if regex.match(value):
                    return True
        return False

    def mightAccept(self, value):
        return self.canTouch(value)

    def accept(self, value, plugin):
        if plugin in self.__regexes.keys():
            for p in self.__regexes[plugin]:
                if p.match(value) is not None:
                    return True
        return False

    def getAcceptingPlugins(self, value):
        accepting = set()
        for plugin in self.__regexes.keys():
            if plugin is not None:
                for r in self.__regexes[plugin]:
                    if r.match(value) is not None:
                        accepting.add(plugin)
                        break
        return accepting

    def setRegex(self, regex, plugin):
        try:
            p = re.compile(regex)
        except sre_constants.error as e:
            raise ConfigurationError("Error on regex %s : %s" %
                                     (regex, str(e))) from e

        if plugin in self.__regexes.keys():
            self.__regexes[plugin].append(p)
        else:
            self.__regexes[plugin] = [p]

    def getAllPlugins(self):
        return self.__regexes.keys()


class Acceptor(object):
    """Acceptor handles the business rules.
    It public API allows to check if a plugin should verify an URI using accept
    method and setter methods used by ConfigLoader.
    """

    def __init__(self, defaultUri=False):
        self.__pluginUri = dict()
        self.__uriDefault = dict()
        self.uris = set()
        self.__positive_uris = set()

    def canTouch(self, value):
        return self.__resolveDefaultAcceptValue(self.getMaxPrefix(value))

    def accept(self, value, pluginId):
        # value je rovnou adresa, nikoliv Transaction
        return self.__resolvePluginAcceptValue(pluginId,
                                               self.getMaxPrefix(value))

    def getMaxPrefix(self, value):
        assert type(value) is str
        # seznam prefixu, pro nas uri chceme nejdelsi prefix
        trie = marisa_trie.Trie(list(self.uris))
        prefList = trie.prefixes(value)

        if len(prefList) > 0:
            return prefList[-1]
        else:
            return value

    def mightAccept(self, value):
        return self.getMaxPrefix(value) in self.__positive_uris

    def __resolvePluginAcceptValue(self, pluginId, uri):
        res = self.__pluginAcceptValue(pluginId, uri)
        if res == Resolution.yes:
            # accept -> pokud neni explicitni match, zakazano
            return True
        else:
            return False

    def __resolveDefaultAcceptValue(self, uri):
        # canTouch -> pokud neni explicitni zakaz, povoleno
        res = self.__resolveFromDefault(uri, self.__uriDefault)
        if res == Resolution.no:
            return False
        else:
            return True

    def __pluginAcceptValue(self, pluginId, uri):
        # existuje pravidlo (plugin, value, X)?
        if pluginId in self.__pluginUri:
            uris = self.__pluginUri[pluginId]
            if uri in uris:
                return Acceptor.getResolution(uris[uri])
            else:
                return Resolution.none
        else:
            return Resolution.none

    @staticmethod
    def __resolveFromDefault(identifier, default):
        # existuje pravidlo (value, X)?
        if identifier in default:
            return Acceptor.getResolution(default[identifier])
        else:
            return Resolution.none

    def setPluginAcceptValue(self, plugin, value, accept):
        if plugin not in self.__pluginUri:
            self.__pluginUri[plugin] = dict()

        values = self.__pluginUri[plugin]
        values[value] = accept
        self.uris.add(value)
        if accept is True:
            self.__positive_uris.add(value)

    def setDefaultAcceptValue(self, uri, value):
        # config loader nastavi True, pokud nekdy videl danou hodnotu v
        # konfiguraci a nebyla zakazana
        # config loader nastavi False, pokud je zakazano se danych hodnot
        # dotykat
        if uri in self.__uriDefault:
            if not self.__uriDefault[uri]:
                return
        self.__uriDefault[uri] = value
        self.uris.add(uri)
        if value:
            self.__positive_uris.add(uri)

    def getValues(self):
        return self.uris

    def getPositiveValues(self):
        return self.__positive_uris

    @staticmethod
    def getResolution(val):
        if val is True:
            return Resolution.yes
        else:
            return Resolution.no

    def reverseValues(self):
        reverse = set()
        positive_reverse = set()
        for value in self.uris:
            reverse.add(value[::-1])
            if value in self.__positive_uris:
                positive_reverse.add(value[::-1])
        self.uris = reverse
        self.__positive_uris = positive_reverse

    def getAllPlugins(self):
        return self.__pluginUri.keys()
