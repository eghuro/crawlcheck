# -*- coding: utf-8 -*-
"""Decision if a transaction is checked by a plugin.

Acceptor module contains business rules to decide if a transaction will be
checked by a plugin.

For a plugin it's possible to set which URIs should be checked and which should
not as well as which content types should be checked and which should not.
In case for an URI or a content type, it's not specified wheather it should be
checked or not, there is a possibility to set up a default.
In case for a plugin there's no configuration at all or it's missing for an URI
or a content type and default for the plugin is not set, there's a global
configuration. Global configuration is similar to a plugin-local configuration,
there are URI and content type specific rules and a default fallback. The only
exception is that the default fallback must be set.
"""
from enum import Enum
import marisa_trie


class Resolution(Enum):
    """Resolution enum helps apply a three state logic in Acceptor.
    Posible resolutions are yes, no or none.
    """

    yes = 1
    no = 2
    none = 3


class Acceptor(object):
    """Acceptor handles the business rules.
    It public API allows to check if a plugin should verify an URI using accept
    method and setter methods used by ConfigLoader.
    """

    def __init__(self, defaultUri=False):
        self.defaultUri = defaultUri
        self.pluginUri = dict()
        self.uriDefault = dict()
        self.uris = set()
        self.positive_uris = set()

    def accept(self, value, pluginId):
        #value je rovnou adresa, nikoliv Transaction
        return self.resolvePluginAcceptValue(pluginId, self.getMaxPrefix(value))

    def getMaxPrefix(self, value):
       assert type(value) is unicode
       # seznam prefixu, pro nas uri chceme nejdelsi prefix
       trie = marisa_trie.Trie(self.uris)
       prefList = trie.prefixes(value)
        
       if len(prefList) > 0:
           return prefList[-1]
        
       else:
           return value

    def mightAccept(self, value):
        return self.getMaxPrefix(value) in self.positive_uris

    def resolvePluginAcceptValue(self, pluginId, uri):
        res = self.pluginAcceptValue(pluginId, uri)
        if res == Resolution.yes:
            return True
        elif res == Resolution.no:
            return False
        else:
            return self.defaultUri #self.resolveDefaultAcceptValue(uri) #TODO: fix in tests?

    def resolveDefaultAcceptValue(self, uri): #used in Transaction.isTouchable
        res = self.resolveFromDefault(uri, self.uriDefault)
        if res == Resolution.yes:
            return True
        elif res == Resolution.no:
            return False
        else:
            return self.defaultUri

    def pluginAcceptValue(self, pluginId, uri):
        if pluginId in self.pluginUri:
            uris = self.pluginUri[pluginId]
            if uri in uris:
                return Acceptor.getResolution(uris[uri])
            else:
                return Resolution.none
        else:
            return Resolution.none

    @staticmethod
    def resolveFromDefault(identifier, default): #from resolveDefaultAcceptValue
        if identifier in default:
            return Acceptor.getResolution(default[identifier])
        else:
            return Resolution.none

    def setPluginAcceptValue(self, plugin, value, accept):
        if plugin not in self.pluginUri:
            self.pluginUri[plugin] = dict()

        values = self.pluginUri[plugin]
        values[value] = accept
        self.uris.add(value)
        if accept is True:
            self.positive_uris.add(value)

    def setDefaultAcceptValue(self, uri, value):
        #config loader nastavi True, pokud nekdy videl danou hodnotu v konfiguraci a nebyla zakazana
        #config loader nastavi False, pokud je zakazano se danych hodnot dotykat
        self.uriDefault[uri] = value
        self.uris.add(uri)
        if value:
            self.positive_uris.add(uri)

    def getValues(self):
        return self.uris

    def getPositiveValues(self):
        return self.positive_uris

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
            if value in self.positive_uris:
                positive_reverse.add(value[::-1])
        self.uris = reverse
        self.positive_uris = positive_reverse
