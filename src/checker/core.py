import marisa_trie
from pluginDBAPI import DBAPI, VerificationStatus
from plugin.common import PluginType, PluginTypeError
import logging
from urlparse import urlparse


class Core:

    def __init__(self, plugins, conf):
        self.plugins = plugins
        self.log = logging.getLogger("crawlcheck")
        self.conf = conf
        self.db = DBAPI(conf.dbconf)

        self.queue = Queue(self.db)
	self.queue.load()

        self.journal = Journal(self.db)
        self.journal.load()

        self.rack = Rack(self.plugins, self.conf.uri_acceptor, self.conf.type_acceptor)

        for entryPoint in self.conf.entry_points:
            self.queue.push(Transaction(entryPoint, 0))

        for plugin in self.plugins:
            self.__initializePlugin(plugin)

    def run(self):
        while not self.queue.isEmpty():
            transaction = self.queue.pop()

            if transaction.depth > self.conf.max_depth:
                continue #skip

            self.log.info("Processing "+transaction.uri)
            try:
                transaction.loadResponse(self.conf)
                self.rack.run(transaction)
            except TouchException, NetworkError:
                self.journal.stopChecking(transaction, VerificationStatus.done_ko)
                raise
            self.journal.stopChecking(transaction, VerificationStatus.done_ok)

    def finalize(self):
        self.queue.store()
        self.journal.store()

    def __initializePlugin(self, plugin):
        plugin.setJournal(self.journal)

        # TODO: refactor to be more Pythonic
        if plugin.type == PluginType.CRAWLER:
            plugin.setQueue(self.queue)
            
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

    def loadResponse(self, conf):
        if self.isTouchable(conf.uri_acceptor):
            try:
                acceptedTypes = self.__get_accepted_types(conf.uri_map, conf.uri_acceptor)
                self.type, self.file = Network.getLink(self, acceptedTypes, conf)
            except NetworkError:
                raise
        else:
            raise TouchException()

    def getContent(self):
        return "" #info.getContent().encode('utf-8')

    def isTouchable(self, uriAcceptor):
        return uriAcceptor.defaultAcceptValue(self.uri) != Resolution.no

    def getStripedUri(self):
        pr = urlparse(self.uri)
        return pr.scheme+'://'+pr.netloc

   def __get_accepted_types(self, uriMap, uriAcceptor):
        if uriMap[self.uri]:
            return uriMap[uriAcceptor.getMaxPrefix(self.uri)]
        else:
            return []


class Rack:

    def __init__(self, plugins = [], uriAcceptor, typeAcceptor, suffixAcceptor):
        self.plugins = plugins
        self.uriAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor
        self.suffixAcceptor = suffixAcceptor

    def run(self, transaction):
        log = logging.getLogger("crawlcheck")
        for plugin in self.plugins:
            if self.__accept(transaction, plugin):
                log.info(plugin.id + " started checking " + transaction.uri)
                plugin.check(transaction)
                log.info(plugin.id + " stopped checking " + transaction.uri)

    def insert(self, plugin):
        self.plugins.append(plugin)

    def __accept(transaction, plugin):
        rotTransaction = transaction
        rotTransaction.uri = transaction.getStripedUri()[::-1]

        return self.typeAcceptor.accept(transaction, plugin.id) and (self.prefixAcceptor.accept(transaction, plugin.id) or self.suffixAcceptor.accept(rotTransaction, plugin.id))

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

    def foundDefect(self, transaction, defect):
        pass

class Defect:


    def __init__(self, name, additional):
        self.name = name
        self.additional = additional

