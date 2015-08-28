""" PluginRunner runs all transactions through applicable checkers.
"""
from pluginDBAPI import DBAPI
import marisa_trie


class PluginRunner(object):
    """ PluginRunner runs all transactions through applicable checkers.
        A transaction is checked by a plugin if it is accepted by both
        uri acceptor and content-type acceptor.
        For acceptors, uri is changed to the longest prefix based on
        plugin's configuration using trie.
    """
    def __init__(self, dbconf, uriAcceptor, typeAcceptor):
        self.dbconf = dbconf
        self.pluginsById = {}
        self.uriAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor

    def runTransaction(self, plugins, info):
        """ Run a single transaction through all plugins where it's accepted.
        """
        print "Verifying "+info.getUri()
        for plugin in plugins:
            if self.accept(plugin.getId(), info):
                print plugin.getId()
                plugin.check(info.getId(), info.getContent())

    def run(self, plugins):
        """ Run all transactions through all plugins where it's accepted.
        """
        api = DBAPI(self.dbconf)
        for plugin in plugins:
            plugin.setDb(api)
            self.pluginsById[plugin.getId()] = plugin
        info = api.getTransaction()
        while info.getId() != -1:
            print "Processing "+info.getUri()
            info.setUri(self.getMaxPrefix(info.getUri()))
            print "Uri changed: "+info.getUri()
            # uri se nahradi nejdelsim prefixem dle konfigurace pluginu
            self.runTransaction(plugins, info)
            api.setFinished(info.getId())
            info = api.getTransaction()

    def accept(self, pluginId, transaction):
       print "Plugin: "+pluginId
       print "URI: "+transaction.getUri()
       print "CType: "+transaction.getContentType() 
       return self.uriAcceptor.accept(pluginId, transaction.getUri()) and self.typeAcceptor.accept(pluginId, transaction.getContentType())

    def getMaxPrefix(self, uri):
        prefixes = self.uriAcceptor.getValues()
        #uPrefixes = []
        #for prefix in prefixes:
          #uPrefixes.add(unicode(prefix,encoding="utf-8"))

        # seznam prefixu, pro nas uri chceme nejdelsi prefix
        trie = marisa_trie.Trie(prefixes)
        prefList = trie.prefixes(unicode(uri, encoding="utf-8"))
        if len(prefList) > 0:
            return prefList[-1]
        else: return uri
