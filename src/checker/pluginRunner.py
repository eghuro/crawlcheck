""" PluginRunner runs all transactions through applicable checkers.
"""

from pluginDBAPI import DBAPI
from plugin.common import PluginType
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
        self.__dbconf = dbconf
        self.__uri_acceptor = uriAcceptor
        self.__type_acceptor = typeAcceptor
        self.__max_depth = maxDepth


    ### PUBLIC API ###
    
    
    def run(self, plugins):
        """ Run all transactions through all plugins where it's accepted.
        """

        print("Running checker")
        api = DBAPI(self.__dbconf)
        
        # initialization
        self.__initialize_plugins(plugins, api)

        # process data
        self.__loop_database(api)


    ### PRIVATE IMPLEMENTATION ###

    def __initialize_plugins(self, plugins, api):
        
        for plugin in plugins:
            plugin.setDb(api)
            
            # TODO: refactor to be more Pythonic
            if plugin.type == PluginType.CRAWLER:
                plugin.setTypes(self.__type_acceptor.getValues())
                plugin.setUris(self.__uri_acceptor.getValues())
                plugin.setMaxDepth(self.__max_depth)
            
            elif plugin.type == PluginType.CHECKER:
                pass
            
            else:
                #FATAL ERROR: unknown plugin type
                #TODO: Raise
                pass


    def __loop_database(self, api):

        info = api.getTransaction()
        
        while info.getId() != -1:
            print("Processing "+info.getUri())
            # uri is replaced by the longest prefix according to configuration
            prefix = self.__get_max_prefix(info.getUri())
            self.__run_transaction(plugins, info, prefix)
            api.setFinished(info.getId())
            info = api.getTransaction()


    @staticmethod
    def __run_plugin(plugin, info):
        plugin.check(info.getId(), info.getContent().encode('utf-8'))


    def __run_transaction(self, plugins, info, prefix):

        """ Run a single transaction through all plugins where it's accepted.
        """

        # create processes to run each plugin        
        # TODO: have processes created back in initialization, only once
        # TODO: only set info here
        processes = self.__create_processes(plugins, info, prefix)

        for process in processes:
            process.start()

        for process in processes:
            process.join()


    def __create_processes(self, plugins, info, prefix):

        processes = []
        
        for plugin in plugins:
            fakeTransaction = info
            fakeTransaction.setUri(prefix)

            if self.__accept(plugin.getId(), fakeTransaction):
                print(plugin.getId())
                
                if plugin.type == PluginType.CRAWLER:
                    plugin.setDepth(info.getDepth())
                
                p = Process(target=PluginRunner.__runPlugin, args=(plugin, info))
                processes.append(p)

        return processes


    def __accept(self, plugId, transaction):
        
        uri = self.__uri_acceptor.accept(plugId, transaction.getUri())
        ctype = self.__type_acceptor.accept(plugId, transaction.getContentType())
        
        return uri and ctype


    def __get_max_prefix(self, uri):
        
        prefixes = self.__uri_acceptor.getValues()

        # seznam prefixu, pro nas uri chceme nejdelsi prefix
        trie = marisa_trie.Trie(prefixes)
        prefList = trie.prefixes(unicode(str(uri), encoding="utf-8"))
        
        if len(prefList) > 0:
            return prefList[-1]
        
        else:
            return uri
