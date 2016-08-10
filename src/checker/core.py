import marisa_trie
from pluginDBAPI import DBAPI, VerificationStatus
from plugin.common import PluginType, PluginTypeError


class Core:

    def __init__(self, plugins):
        self.plugins = plugins

    def initialize(self, uriAcceptor, typeAcceptor, db, entryPoints, maxDepth):
        self.db = DBAPI(db)
        self.uriAcceptor = uriAcceptor

        self.queue = Queue(self.db)
	self.queue.load()

        self.journal = Journal(self.db)
        self.journal.load()

        self.rack = Rack(self.plugins, uriAcceptor, typeAcceptor)

        for entryPoint in entryPoints:
            self.queue.push(Transaction(entryPoint, 0))

        for plugin in self.plugins:
            self.__initializePlugin(plugin, typeAcceptor, uriAcceptor, maxDepth)

    def run(self):
        while not self.queue.isEmpty():
            transaction = self.queue.pop()
            try:
                transaction.loadResponse(self.uriAcceptor, self.journal)
                self.rack.run(transaction)
            except TouchException, NetworkError:
                self.journal.stopChecking(transaction, VerificationStatus.done_ko)
                raise
            self.journal.stopChecking(transaction, VerificationStatus.done_ok)

    def finalize(self):
        self.queue.store()
        self.journal.store()

    def __initializePlugin(self, plugin, typeAcceptor, uriAcceptor, maxDepth):
        plugin.setJournal(self.journal)

        # TODO: refactor to be more Pythonic
        if plugin.type == PluginType.CRAWLER:
            plugin.setTypes(typeAcceptor.getValues())
            plugin.setUris(uriAcceptor.getValues())
            
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
       self.trId = -1 #TODO

   def loadResponse(self, uriAcceptor, journal):
       if self.isTouchable(uriAcceptor):
           try:
               self.type, self.file = Network.getLink(self.uri, self, journal)
           except NetworkError:
               raise
       else:
           raise TouchException()

   def getContent(self):
        return "" #info.getContent().encode('utf-8')

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
            fakeTransaction = transaction
            fakeTransaction.uri = transaction.getMaxPrefix(uriAcceptor)
            if self.__accept(fakeTransaction, plugin):
                plugin.check(transaction)

    def insert(self, plugin):
        self.plugins.append(plugin)

    def __accept(fakeTransaction, plugin):
        return self.typeAcceptor.accept(fakeTransaction, plugin.getId()) and self.uriAcceptor.accept(fakeTransaction, plugin.getId())

class Queue:

    def __init__(self, db):
        self.db = db

    def isEmpty(self):
        pass

    def pop(self):
        pass  

    def push(self, transaction, parent=None):
        pass

    def load(self):
        pass

    def store(self):
        pass

class Journal:


    def __init__(self, db):
        self.db = db

    def load(self):
        pass

    def store(self):
        pass

    def startChecking(self, transaction):
        pass

    def stopChecking(self, transaction, status):
        pass

    def foundLink(self, transaction, link):
        pass

    def foundDefect(self, transaction, defect):
        pass

class Defect:


    def __init__(self, name, additional):
        self.name = name
        self.additional = additional

