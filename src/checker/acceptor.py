from enum import Enum

class Resolution(Enum):
    yes = 1
    no = 2
    none = 3

class Acceptor:
    def __init__(self, defaultUri):
        self.defaultUri = defaultUri
        self.pluginUri = dict()
        self.pluginUriDefault = dict()
        self.uriDefault = dict()
        self.uris = set()

    def accept(self, pluginId, uri):
        res = self.pluginAcceptUri(pluginId, uri)
        if res == Resolution.yes:
            return True
        elif res == Resolution.no:
            return False
        else:
	    res = self.pluginAcceptUriDefault(pluginId)
            if res == Resolution.yes:
                return True
            elif res == Resolution.no:
                return False
            else:
                res = self.defaultAcceptUri(uri)
                if res == Resolution.yes:
                    return True
                elif res == Resolution.no:
                    return False
                else:
                    return self.defaultUri

    def pluginAcceptUri(self, pluginId, uri):
        if pluginId in self.pluginUri:
            uris = self.pluginUri[pluginId]
            if uri in uris:
                return self._getResolution(uris[uri])
            else:
                return Resolution.none
        else:
            return Resolution.none

    def pluginAcceptUriDefault(self, pluginId):
        if pluginId in self.pluginUriDefault:
            return self._getResolution(self.pluginUriDefault[pluginId])
        else:
            return Resolution.none

    def defaultAcceptUri(self, uri):
        if uri in self.uriDefault:
            return self._getResolution(self.uriDefault[uri])
        else:
            return Resolution.none

    def setPluginAccepValue(self, plugin, value, accept):
        if plugin not in self.pluginUri:
            self.pluginUri[plugin] = dict()
 
        values = self.pluginUri[pluginId]
        values[value] = accept
        self.uris.add(value)

    def setPluginAcceptValueDefault(self, plugin, accept):
        self.pluginUriDefault[plugin] = accept

    def setDefaultAcceptValue(self, uri, value):
        self.uriDefault[uri] = value
        self.uris.add(uri)

    def getValues(self):
        return self.uris

    def _getResolution(self, yes):
        if yes:
          return Resolution.yes
        else:
          return Resolution.no
