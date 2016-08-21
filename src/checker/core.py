import marisa_trie
import logging
import Queue
from urlparse import urlparse
from copy import deepcopy
from multiprocessing import Pool, Process
from pluginDBAPI import DBAPI, VerificationStatus
from plugin.common import PluginType, PluginTypeError
from net import Network, NetworkError




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

        self.rack = Rack(self.conf.uri_acceptor, self.conf.type_acceptor, self.plugins)

        for entryPoint in self.conf.entry_points:
            self.queue.push(createTransaction(entryPoint, 0))

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
        if plugin.type == PluginType.CRAWLER:
            plugin.setQueue(self.queue)


class TouchException(Exception):

    pass


class Transaction:

    def __init__(self, uri, depth, srcId, idno):
        #Use the factory method below!!
        self.uri = uri
        self.depth = depth
        self.type = None
        self.file = None
        self.idno = idno

    def loadResponse(self, conf):
        if self.isTouchable(conf.uri_acceptor, conf.suffix_acceptor):
            try:
                acceptedTypes = self.getAcceptedTypes(conf)
                self.type, self.file = Network.getLink(self, acceptedTypes, conf)
            except NetworkError:
                raise
        else:
            raise TouchException()

    def getContent(self):
        with open(self.file, 'r') as f:
            data = f.read()
            return data.encode('utf-8')

    def isTouchable(self, uriAcceptor, suffixAcceptor):
        return uriAcceptor.resolveDefaultAcceptValue(self.uri) and suffixAcceptor.resolveDefaultAcceptValue(self.uri[::-1])

    def getStripedUri(self):
        pr = urlparse(self.uri)
        return pr.scheme+'://'+pr.netloc

    def __get_accepted_types(self, uriMap, uriAcceptor):
        if self.uri in uriMap:
            if uriMap[self.uri]:
                return uriMap[uriAcceptor.getMaxPrefix(self.uri)]
        return []
 

    def getAcceptedTypes(self, conf):
        if conf is None:
            return []
        if conf.uri_map is None:
            return []
        acceptedTypes = self.__get_accepted_types(conf.uri_map, conf.uri_acceptor)
        bak = self.uri
        self.uri = self.uri[::-1]
        acceptedTypes += self.__get_accepted_types(conf.suffix_uri_map, conf.suffix_acceptor)
        self.uri = bak
        return acceptedTypes

transactionId = 0
def createTransaction(uri, depth = 0, srcId = -1):
    global transactionId
    tr = Transaction(uri, depth, srcId, transactionId)
    transactionId = transactionId + 1
    return tr


class Rack:

    def __init__(self, uriAcceptor, typeAcceptor, suffixAcceptor, plugins = []):

        self.plugins = plugins
        self.uriAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor
        self.suffixAcceptor = suffixAcceptor
        self.log = logging.getLogger("crawlcheck")

    def run(self, transaction):
 
        for plugin in self.plugins:
            self.__run_one(transaction, plugin)

    def __run_one(self, transaction, plugin):

        if self.accept(transaction, plugin):
            self.log.info(plugin.id + " started checking " + transaction.uri)
            plugin.check(transaction)
            self.log.info(plugin.id + " stopped checking " + transaction.uri)

    def accept(transaction, plugin):

        rotTransaction = deepcopy(transaction)
        rotTransaction.uri = transaction.getStripedUri()[::-1]
        return self.typeAcceptor.accept(transaction, plugin.id) and ( self.prefixAcceptor.accept(transaction, plugin.id) or self.suffixAcceptor.accept(rotTransaction, plugin.id) )


class ParallelRack(Rack):

    def __init__(self, prefixAcceptor, typeAcceptor, suffixAcceptor, plugins = []):

        Rack.__init__(uriAcceptor, typeAcceptor, suffixAcceptor, plugins)
        self.__count = count
        self.__pool = []
        for plugin in plugins: #TODO: refactor - process count per plugin in conf
            p = Worker(self.log, typeAcceptor, prefixAcceptor, suffixAcceptor, plugin)
            self.__pool.append(p)
            p.start()
        for plugin in plugins:
            p.join()

    def run(self, transaction):

        for worker in self.__pool:
            if self.accept(transaction, worker.plugin):
                worker.register(transaction)


class Worker(Process):

    def __init__(self, initialize (log, typeAcceptor, prefixAcceptor, suffixAcceptor, plugin, db):

        super(Worker, self).__init__()
        self.log = log
        self.typeAcceptor = typeAcceptor
        self.prefixAcceptor = prefixAcceptor
        self.suffixAcceptor = suffixAcceptor
        self.plugin = plugin
        self.queue = Queue()

    def run(self):

        #TODO: loop; wait for queue
        #TODO: finalizer???
        transaction = self.queue.pop()
        self.log.info(plugin.id + " started checking " + transaction.uri)
        self.plugin.check(transaction)
        self.log.info(plugin.id + " stopped checking " + transaction.uri)

    def register(self, transaction):

        self.log.info(plugin.id + " will check " + transaction.uri)
        self.queue.push(transaction)


class Queue:


    def __init__(self, db):
        self.__db = db
        self.__q = Queue.Queue()
        self.__parent = Dict()

    def isEmpty(self):
        return self.__q.empty()

    def pop(self):
        return self.__q.get()

    def push(self, transaction, parent=None):
        self.__q.put(transaction)
        if parent is not None:
            self.__parent[transaction.idno] = parent.idno
        #write into in-memory DB

    def load(self):
        pass

    def store(self):
        pass

class Journal:


    def __init__(self, db):
        self.__db = db

    def load(self):
        #copy on-disk to in-memory
        pass

    def store(self):
        #copy in-memory on disk
        pass


    #always write into in-memory DB
    def startChecking(self, transaction):
        pass

    def stopChecking(self, transaction, status):
        pass

    def foundDefect(self, transaction, defect):
        pass

    def foundDefect(self, transaction, name, additional):
        pass

class Defect:


    def __init__(self, name, additional):
        self.name = name
        self.additional = additional

