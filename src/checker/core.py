import marisa_trie
from pluginDBAPI import DBAPI
from plugin.common import PluginType, PluginTypeError


class Core:

    def __init__(self, plugins):
        self.plugins = plugins

    def initialize(self, uriAcceptor, typeAcceptor, db, entryPoints, maxDepth):
        self.queue = Queue(db)
        self.rack = Rack(self.plugins, uriAcceptor, typeAcceptor)
        self.db = DBAPI(db)
        self.uriAcceptor = uriAcceptor

        for entryPoint in entryPoints:
            self.queue.push(Transaction(entryPoint, 0))

        for plugin in self.plugins:
            self.__initializePlugin(plugin, typeAcceptor, uriAcceptor, maxDepth)

    def run(self):
        while not self.queue.isEmpty():
            transaction = self.queue.pop()
            try:
                transaction.loadResponse(self.uriAcceptor, self.db) #DB potrebuji pro zapsani pripadnych defektu
                self.rack.run(transaction)
            except TouchException:
                raise
            except NetworkError:
                raise
            #nastavit setFinished, refaktorovat na stavy: neprobehlo, probiha, probehlo uspesne, probehlo neuspesne

    def finalize(self):
        pass

    def __initializePlugin(self, plugin, typeAcceptor, uriAcceptor, maxDepth):
        plugin.setDb(self.db)

        # TODO: refactor to be more Pythonic
        if plugin.type == PluginType.CRAWLER:
            plugin.setTypes(typeAcceptor.getValues())
            plugin.setUris(uriAcceptor.getValues())
            plugin.setMaxDepth(maxDepth)
            
        elif plugin.type == PluginType.CHECKER:
            pass
            
        else:
            #FATAL ERROR: unknown plugin type
            raise PluginTypeError


class TouchException(Exception):

    pass


class Transaction:

   def __init__(self, uri, depth, srcId = -1):
       self.uri = uri
       self.depth = depth
       self.type = None
       self.file = None
       self.srcId = srcId

   def loadResponse(self, uriAcceptor, db):
       if self.isTouchable(uriAcceptor):
           try:
               self.type, self.file = Network.getLink(self.uri, self.srcId, db)
           except NetworkError:
               raise
       else:
           raise TouchException()

   def isTouchable(self, uriAcceptor):
       return uriAcceptor.defaultAcceptValue(self.uri) != Resolution.no

   def getMaxPrefix(self, uriAcceptor):
        
       prefixes = uriAcceptor.getValues()

       # seznam prefixu, pro nas uri chceme nejdelsi prefix
       trie = marisa_trie.Trie(prefixes)
       prefList = trie.prefixes(unicode(str(self.uri), encoding="utf-8"))
        
       if len(prefList) > 0:
           return prefList[-1]
        
       else:
           return uri


class Rack:

    def __init__(self, plugins = [], uriAcceptor, typeAcceptor):
        self.plugins = plugins
        self.uriAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor

    def run(self, transaction):
        for plugin in self.plugins:
            if self.typeAcceptor.accept(transaction, plugin) and self.uriAcceptor.accept(transaction, plugin): #TODO: acceptory si zavolaji getMaxPrefix(), pouzivaji transaction
                if plugin.type == PluginType.CRAWLER:
                    plugin.setDepth(transaction.depth)
                plugin.check(transaction) #TODO: plugin nepouziva novou transaction, ale stare DBAPI->transaction info

    def insert(self, plugin):
        self.plugins.append(plugin)

class Queue:

    def __init__(self, db):
        pass

    def isEmpty(self):
        pass

    def pop(self):
        pass

    def push(self, transaction, parent=None):
        pass