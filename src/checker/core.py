import logging
import queue
import urllib.parse
import os
from urllib.parse import urlparse
from pluginDBAPI import DBAPI, VerificationStatus, Table
from common import PluginType, PluginTypeError
from net import Network, NetworkError, ConditionError, StatusError
from filter import FilterException #, DepthFilter, RobotsFilter, ContentLengthFiler




class Core:

    def __init__(self, plugins, filters, headers, conf):           
        self.plugins = plugins
        self.log = logging.getLogger()
        self.conf = conf
        self.db = DBAPI(conf.dbconf)
        self.db.load_defect_types()
        self.db.load_finding_id()
        self.files = []

        self.filters = filters #[DepthFilter(conf), RobotsFilter(conf)]
        self.header_filters = headers #[ContentLengthFiler(conf)]

        TransactionQueue.initialize()
        self.queue = TransactionQueue(self.db)
        self.queue.load()

        Journal.initialize()
        self.journal = Journal(self.db)

        for plugin in self.plugins:
            self.__initializePlugin(plugin)

        for entryPoint in self.conf.entry_points:
            self.queue.push(createTransaction(entryPoint.url, 0, -1, entryPoint.method, entryPoint.data))

        self.rack = Rack(self.conf.uri_acceptor, self.conf.type_acceptor, self.conf.suffix_acceptor, plugins)

    def run(self):
        #Queue
        while not self.queue.isEmpty():
            try:
                transaction = self.queue.pop()
            except queue.Empty:
                continue

            if not transaction.isWorthIt(self.conf):
                self.log.debug(transaction.uri+" not worth my time")
                self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue

            #Custom filters
            try:
                for tf in self.filters:
                    tf.filter(transaction)
            except FilterException:
                self.log.debug(transaction.uri + " filtered out")
                self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue
            self.log.info("Processing "+transaction.uri)

            #Networking
            try:
                transaction.loadResponse(self.conf, self.journal, self.header_filters)
            except TouchException: #nesmim se toho dotykat
                self.log.debug("Forbidden to touch "+transaction.uri)
                self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue
            except ConditionError:
               self.log.debug("Condition failed")
               self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
               continue
            except FilterException: #header filters
                self.log.debug(transaction.uri + " filtered out")
                self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue
            except StatusError as e:
               self.log.debug("Status error: "+str(e))
               self.journal.stopChecking(transaction, VerificationStatus.done_ko)
               continue
            except NetworkError as e:
                self.log.error("Network error: "+str(e))
                self.journal.stopChecking(transaction, VerificationStatus.done_ko)
                continue

            else: #Plugins
                self.files.append(transaction.file)
                self.journal.startChecking(transaction)
                self.rack.run(transaction)
                self.journal.stopChecking(transaction, VerificationStatus.done_ok)

    def finalize(self):
        self.rack.stop()
        try:
            self.db.sync()
        except:
            self.rack.stop()
        finally:
            self.clean_tmps()

    def clean_tmps(self):
        for filename in self.files:
            try:
                os.remove(filename)
            except OSError:
                continue

    def __initializePlugin(self, plugin):
        plugin.setJournal(self.journal)
        if plugin.category == PluginType.CRAWLER:
            plugin.setQueue(self.queue)
        elif plugin.category == PluginType.CHECKER:
            pass
        else:
            raise PluginTypeError


class TouchException(Exception):

    pass


class Transaction:

    def __init__(self, uri, depth, srcId, idno, method="GET", data=None):
        #Use the factory method below!!
        self.uri = uri
        self.depth = depth
        self.type = None
        self.file = None
        self.idno = idno
        self.srcId = srcId
        self.method = method
        self.data = data
        #self.log = logging.getLogger()

    def loadResponse(self, conf, journal, filters):
        if self.isTouchable(conf.uri_acceptor, conf.suffix_acceptor):
            try:
                acceptedTypes = self.getAcceptedTypes(conf)
                self.type, self.file = Network.getLink(self, acceptedTypes, conf, journal, filters)
            except (NetworkError, ConditionError, StatusError):
                raise
        else:
            raise TouchException()

    def getContent(self):
        with open(self.file, 'r') as f:
            data = f.read()
            return data

    def isTouchable(self, uriAcceptor, suffixAcceptor):
        up = uriAcceptor.getMaxPrefix(self.uri)
        striped = self.getStripedUri()
        sp = suffixAcceptor.getMaxPrefix(striped[::-1])
        prefix = uriAcceptor.resolveDefaultAcceptValue(up)
        suffix = suffixAcceptor.resolveDefaultAcceptValue(sp)
        return prefix or suffix

    def getStripedUri(self):
        pr = urlparse(self.uri)
        return str(pr.scheme+'://'+pr.netloc)

    def __get_accepted_types(self, uriMap, uriAcceptor):
        p = uriAcceptor.getMaxPrefix(self.uri)
        if p in uriMap:
            if uriMap[p]:
                return uriMap[p]
        return []
 

    def getAcceptedTypes(self, conf):
        if conf is None:
            return []
        
        if conf.uri_map is None:
            acceptedTypes = []
        else:
            acceptedTypes = Transaction.__set2list(self.__get_accepted_types(conf.uri_map, conf.uri_acceptor))
        
        bak = self.uri
        self.uri = self.uri[::-1]
        if conf.suffix_uri_map is not None:
             acceptedTypes += Transaction.__set2list(self.__get_accepted_types(conf.suffix_uri_map, conf.suffix_acceptor))
        self.uri = bak
        return acceptedTypes

    def isWorthIt(self, conf):
        return conf.uri_acceptor.mightAccept(self.uri) or conf.suffix_acceptor.mightAccept(self.getStripedUri()[::-1])

    @staticmethod
    def __set2list(x):
        y = []
        for z in x:
          y.append(z)
        return y

transactionId = 0
def createTransaction(uri, depth = 0, parentId = -1, method = 'GET', params=None):
    assert (params is dict) or (params is None)
    global transactionId
    decoded = str(urllib.parse.unquote(urllib.parse.unquote(uri)))
    tr = Transaction(decoded, depth, parentId, transactionId, method, params)
    transactionId = transactionId + 1
    return tr


class Rack:

    def __init__(self, uriAcceptor, typeAcceptor, suffixAcceptor, plugins = []):

        self.plugins = plugins
        self.prefixAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor
        self.suffixAcceptor = suffixAcceptor
        self.log = logging.getLogger()

    def run(self, transaction):
 
        for plugin in self.plugins:
            self.__run_one(transaction, plugin)

    def __run_one(self, transaction, plugin):

        if self.accept(transaction, plugin):
            self.log.info(plugin.id + " started checking " + transaction.uri)
            plugin.check(transaction)
            self.log.info(plugin.id + " stopped checking " + transaction.uri)

    def accept(self, transaction, plugin):

        rot = transaction.getStripedUri()[::-1]
        type_cond = self.typeAcceptor.accept(str(transaction.type), plugin.id)
        prefix_cond = self.prefixAcceptor.accept(transaction.uri, plugin.id)
        suffix_cond = self.suffixAcceptor.accept(rot, plugin.id)
        return type_cond and ( prefix_cond or suffix_cond )

    def stop(self):
        pass

class TransactionQueue:


    status_ids = dict()
    
    @staticmethod
    def initialize():
        TransactionQueue.status_ids["requested"] = 1
        TransactionQueue.status_ids["processing"] = 2

    def __init__(self, db):
        self.__db = db
        self.__seen = set()
        self.__q = queue.Queue()
        
    def isEmpty(self):
        return self.__q.empty()

    def pop(self):
        try:
            t = self.__q.get(block=True, timeout=1)
        except queue.Empty:
            raise
        else:
            self.__db.log(Table.transactions, ('UPDATE transactions SET verificationStatusId = ? WHERE id = ?', [str(TransactionQueue.status_ids["processing"]), t.idno]) )
            self.__db.log(Table.link_defect, ('UPDATE link SET processed = ? WHERE toUri = ?', [str("true"), str(t.uri)] ))
            return t

    def push(self, transaction, parent=None):
        if transaction.uri not in self.__seen:
            self.__seen.add(transaction.uri)
            self.__q.put(transaction)
            self.__db.log(Table.transactions,
                          ('INSERT INTO transactions (id, method, uri, origin, verificationStatusId, depth) VALUES (?, ?, ?, \'CHECKER\', ?, ?)', 
                          [str(transaction.idno), transaction.method, transaction.uri, str(TransactionQueue.status_ids["requested"]), str(transaction.depth)]) )

        if parent is not None:
            self.__db.log_link(parent.idno, transaction.uri, transaction.idno)

    def push_link(self, uri, parent):
        self.push(createTransaction(uri,parent.depth+1, parent.idno), parent)

    def load(self):
        #load transactions from DB to memory - only where status is requested
        for t in self.__db.get_requested_transactions():
            #uri = t[0]; depth = t[1]; idno = t[3]
            srcId = -1
            if t[2] is not None:
                srcId = t[2]
            decoded = str(urllib.parse.unquote(urllib.parse.unquote(t[0])), 'utf-8')
            self.__q.put(Transaction(decoded, t[1], srcId, t[3]))
        #load uris from transactions table for list of seen URIs
        self.__seen.update(self.__db.get_seen_uris())
        #set up transaction id for factory method
        transactionId = self.__db.get_max_transaction_id() + 1

class Journal:


    status_ids = dict()
    
    @staticmethod
    def initialize():
        Journal.status_ids["verifying"] = 3

    def __init__(self, db):
        self.__db = db
       
    def startChecking(self, transaction):
        self.__db.log(Table.transactions, ('UPDATE transactions SET verificationStatusId = ? WHERE id = ?', [str(Journal.status_ids["verifying"]), transaction.idno]) )

    def stopChecking(self, transaction, status):
        self.__db.log(Table.transactions, ('UPDATE transactions SET verificationStatusId = ? WHERE id = ?', [str(status), transaction.idno]) )

    def foundDefect(self, transaction, defect, evidence):
        self.foundDefect(transaction.idno, defect.name, defect.additional, evidence)

    def foundDefect(self, trId, name, additional, evidence, severity = 0.5):
        assert type(trId) == int
        self.__db.log_defect(trId, name, additional, evidence, severity)

    def getKnownDefectTypes(self):
        return self.__db.get_known_defect_types()

class Defect:


    def __init__(self, name, additional = None):
        self.name = name
        self.additional = additional

