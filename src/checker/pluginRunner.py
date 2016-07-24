""" PluginRunner runs all transactions through applicable checkers.
"""
from pluginDBAPI import DBAPI
import marisa_trie
from multiprocessing import Process


class PluginRunner(object):
    """ PluginRunner runs all transactions through applicable checkers.
        A transaction is checked by a plugin if it is accepted by both
        uri acceptor and content-type acceptor.
        For acceptors, uri is changed to the longest prefix based on
        plugin's configuration using trie.
    """
    def __init__(self, dbconf, uriAcceptor, typeAcceptor, maxDepth):
        self.dbconf = dbconf
        self.pluginsById = {}
        self.uriAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor
        self.maxDepth = maxDepth

    @staticmethod
    def runPlugin(plugin, info):
        plugin.check(info.getId(), info.getContent().encode('utf-8'))

    def runTransaction(self, plugins, info, prefix):
        """ Run a single transaction through all plugins where it's accepted.
        """
        # get list of plugins to use
        # create processes to run each plugin
        processes = []
        for plugin in plugins:
            fakeTransaction = info
            fakeTransaction.setUri(prefix)
            if self.accept(plugin.getId(), fakeTransaction):
                print(plugin.getId())
                if self.special_setup(plugin.getId()):
                    plugin.setDepth(info.getDepth())
                    plugin.setMaxDepth(self.maxDepth)
                p = Process(target=PluginRunner.runPlugin, args=(plugin, info))
                processes.append(p)
        for process in processes:
            process.start()
        for process in processes:
            process.join()

    def special_setup(self, pluginId):
        return (pluginId == "linksFinder") or (pluginId == "formChecker")

    def run(self, plugins):
        """ Run all transactions through all plugins where it's accepted.
        """

        print("Running checker")
        api = DBAPI(self.dbconf)
        for plugin in plugins:
            plugin.setDb(api)
            self.pluginsById[plugin.getId()] = plugin
            if plugin.getId() == "linksFinder":
                plugin.setTypes(self.typeAcceptor.getValues())
                plugin.setUris(self.uriAcceptor.getValues())

        info = api.getTransaction()
        while info.getId() != -1:
            print("Processing "+info.getUri())
            prefix = self.getMaxPrefix(info.getUri())
            # uri se nahradi nejdelsim prefixem dle konfigurace pluginu
            self.runTransaction(plugins, info, prefix)
            api.setFinished(info.getId())
            info = api.getTransaction()

    def accept(self, plugId, transaction):
        uri = self.uriAcceptor.accept(plugId, transaction.getUri())
        ctype = self.typeAcceptor.accept(plugId, transaction.getContentType())
        return uri and ctype

    def getMaxPrefix(self, uri):
        prefixes = self.uriAcceptor.getValues()

        # seznam prefixu, pro nas uri chceme nejdelsi prefix
        trie = marisa_trie.Trie(prefixes)
        prefList = trie.prefixes(unicode(str(uri), encoding="utf-8"))
        if len(prefList) > 0:
            return prefList[-1]
        else:
            return uri
