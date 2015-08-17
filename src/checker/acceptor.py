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

    def accept(self, pluginId, uri):
        res = pluginAcceptUri(pluginId, uri)
        if res == Resolution.yes:
            return True
        elif res == Resolution.no:
            return False
        else:
	    res = pluginAcceptUriDefault(pluginId)
            if res == Resolution.yes:
                return True
            elif res == Resolution.no:
                return False
            else:
                res = defaultAcceptUri(uri)
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
                return _getResolution(uris[uri])
            else:
                return Resolution.none
        else:
            return Resolution.none

    def pluginAcceptUriDefault(self, pluginId):
        if pluginId in self.pluginUriDefault:
            return _getResolution(self.pluginUriDefault[pluginId])
        else:
            return Resolution.none

    def defaultAcceptUri(self, uri):
        if uri in self.uriDefault:
            return _getResolution(self.uriDefault[uri])
        else:
            return Resolution.none

    def _getResolution(self, yes):
        if yes:
          return Resolution.yes
        else:
          return Resolution.no
