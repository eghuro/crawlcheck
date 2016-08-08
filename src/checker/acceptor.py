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

    def __init__(self, defaultUri):
        self.defaultUri = defaultUri
        self.pluginUri = dict()
        self.pluginUriDefault = dict()
        self.uriDefault = dict()
        self.uris = set()

    def accept(self, transaction, pluginId):
        """ Does a plugin accept an URI?
        Main API method, that runs a resolution algorithm.
        """

        return self.resolvePluginAcceptValue(pluginId, transaction.uri)

    def resolvePluginAcceptValue(self, pluginId, uri):
        res = self.pluginAcceptValue(pluginId, uri)
        if res == Resolution.yes:
            return True
        elif res == Resolution.no:
            return False
        else:
            return self.resolvePluginAcceptValueDefault(pluginId, uri)

    def resolvePluginAcceptValueDefault(self, pluginId, uri):
        res = self.pluginAcceptValueDefault(pluginId)
        if res == Resolution.yes:
            return True
        elif res == Resolution.no:
            return False
        else:
            return self.resolveDefaultAcceptValue(uri)

    def resolveDefaultAcceptValue(self, uri):
        res = self.defaultAcceptValue(uri)
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

    def pluginAcceptValueDefault(self, pluginId):
        return Acceptor.resolveFromDefault(pluginId, self.pluginUriDefault)

    def defaultAcceptValue(self, uri):
        return Acceptor.resolveFromDefault(uri, self.uriDefault)

    @staticmethod
    def resolveFromDefault(identifier, default):
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

    def setPluginAcceptValueDefault(self, plugin, accept):
        self.pluginUriDefault[plugin] = accept

    def setDefaultAcceptValue(self, uri, value):
        self.uriDefault[uri] = value
        self.uris.add(uri)

    def getValues(self):
        return self.uris

    @staticmethod
    def getResolution(yes):
        if yes is True:
            return Resolution.yes
        else:
            return Resolution.no
