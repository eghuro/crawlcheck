# -*- coding: utf-8 -*-
"""Decision if a transaction is checked by a plugin.

Acceptor module contains budiness rules to decide if a transaction will be
checked by a plugin.
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

    def accept(self, pluginId, uri):
        res = self.pluginAcceptValue(pluginId, uri)
        if res == Resolution.yes:
            return True
        elif res == Resolution.no:
            return False
        else:
            res = self.pluginAcceptValueDefault(pluginId)
            if res == Resolution.yes:
                return True
            elif res == Resolution.no:
                return False
            else:
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
        if pluginId in self.pluginUriDefault:
            return Acceptor.getResolution(self.pluginUriDefault[pluginId])
        else:
            return Resolution.none

    def defaultAcceptValue(self, uri):
        if uri in self.uriDefault:
            return Acceptor.getResolution(self.uriDefault[uri])
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
