from pluginDBAPI import DBAPI
from acceptor import Acceptor
import marisa_trie

class PluginRunner:
    def __init__(self, dbconf, uriAcceptor, typeAcceptor):
        self.dbconf = dbconf
        self.pluginsById = {}
        self.uriAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor

    def runTransaction(self, plugins, info):
        for plugin in plugins:
            if self.accept(plugin.getId(), info):
                plugin.check(info.getId(), info.getContent())

    def run(self, plugins):
        api = DBAPI(self.dbconf)
        for plugin in plugins:
            plugin.setDb(api)
            self.pluginsById[plugin.getId()] = plugin
        info = api.getTransaction()
        while info.getId() != -1:
            info.setUri(self.getMaxPrefix(info.getUri())) # nahradi uri nejdelsim prefixem dle konfigurace pluginu
            self.runTransaction(plugins, info)
            api.setFinished(info.getId())
            info = api.getTransaction()

    def accept(self, pluginId, transaction):
        return self.uriAcceptor.accept(pluginId, transaction.getUri()) & self.typeAcceptor.accept(pluginId, transaction.getContentType())

    def getMaxPrefix(self, uri):
        prefixes = self.uriAcceptor.getValues() # seznam prefixu, pro nas uri chceme nejdelsi prefix
        trie = marisa_trie.Trie(prefixes)
        return trie.prefixes(uri)[-1]

#        return marisa_trie.Trie(self.uriAcceptor.getValues()).prefixes(uri)[-1]
