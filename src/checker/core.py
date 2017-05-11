import logging
import queue
import urllib.parse
import os
import time
import copy
import codecs
import requests
from urllib.parse import urlparse, ParseResult
from pluginDBAPI import DBAPI, VerificationStatus, Table
from common import PluginType, PluginTypeError
from net import Network, NetworkError, ConditionError, StatusError
from filter import FilterException
import gc



class Core:

    def __init__(self, plugins, filters, headers, postprocess, conf):
        self.plugins = plugins
        self.log = logging.getLogger(__name__)
        self.conf = conf
        self.db = DBAPI(conf.dbconf)
        self.db.load_defect_types()
        self.db.load_finding_id()
        self.files = []
        self.__time_subscribers = []
        self.volume = 0

        self.filters = filters
        for f in filters:
            try:
                self.__time_subscribers.append(f.getTimeSubscriber())
            except AttributeError:
                pass
        self.header_filters = headers
        self.postprocessers = postprocess

        self.queue = TransactionQueue(self.db, self.conf)
        self.queue.load()

        self.journal = Journal(self.db)

        for plugin in self.plugins+headers+filters+postprocess:
            self.__initializePlugin(plugin)

        for entryPoint in self.conf.entry_points:
            self.log.debug("Pushing to queue: "+entryPoint.url+", data: "+str(entryPoint.data))
            self.queue.push(createTransaction(entryPoint.url, 0, -1, entryPoint.method, entryPoint.data))

        self.rack = Rack(self.conf.type_acceptor, self.conf.regex_acceptor, plugins)

    def run(self):
        with requests.Session() as session:
            self.__run(session)

    def __run(self, session):
        #Queue
        while not self.queue.isEmpty():
            try:
                transaction = self.queue.pop()
            except queue.Empty:
                continue

            try:
                if type(transaction.uri) != str:
                    transaction.uri = str(transaction.uri)

                self.log.info("Processing " + transaction.uri)

                if not transaction.isWorthIt(self.conf): #neni zadny plugin, ktery by prijal
                    self.log.debug(transaction.uri+" not worth my time")

                    self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
                    continue

                #Custom filters: depth, robots.txt
                for tf in self.filters:
                    tf.filter(transaction)

                r = transaction.testLink(self.conf, self.journal, session) #HEAD, pokud neni zakazan

                #custom HTTP header filters, incl. test if ct matches expectation
                for hf in self.header_filters:
                   hf.filter(transaction, r)

                start = time.time()
                transaction.loadResponse(self.conf, self.journal, session)
            except TouchException: #nesmim se toho dotykat
                self.log.debug("Forbidden to touch "+transaction.uri)
                self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue
            except ConditionError: #URI nebo content-type dle konfigurace
               self.log.debug("Condition failed")
               self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
               continue
            except FilterException: #filters
                self.log.debug(transaction.uri + " filtered out")
                self.journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue
            except StatusError as e: #already logged
               self.journal.stopChecking(transaction, VerificationStatus.done_ko)
               continue
            except NetworkError as e:
                self.log.error("Network error: "+format(e))
                self.journal.stopChecking(transaction, VerificationStatus.done_ko)
                continue

            else: #Plugins
                for sub in self.__time_subscribers:
                    sub.markStart(start, transaction.uri)
                self.files.append(transaction.file)
                self.volume = self.volume + os.path.getsize(transaction.file) 
                self.journal.startChecking(transaction)
                self.rack.run(transaction)
                self.journal.stopChecking(transaction, VerificationStatus.done_ok)
                while self.volume > self.conf.getProperty("maxVolume"):
                    self.log.debug("CLEANUP ... Size of tmps: " + str(self.volume) + ", limit: " + str(self.conf.getProperty("maxVolume")))
                    f = self.files[0]
                    l = os.path.getsize(f)
                    os.remove(f)
                    self.volume = self.volume - l
                    self.files.pop(0)
                    self.log.debug("Size of tmps after cleanup: " + str(self.volume))
                    gc.collect()

    def finalize(self):
        #self.rack.stop()
        self.log.debug("Finalizing")
        try:
            #write to database
            self.db.sync()
        except:
            pass
        finally:
            #clean tmp files
            self.clean_tmps()
            gc.collect()
            #run postprocessing
            self.postprocess()

    def postprocess(self):
        self.log.info("Postprocessing")
        for pp in self.postprocessers:
            self.log.debug(pp.id)
            pp.process()

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
        elif (plugin.category == PluginType.FILTER) or (plugin.category == PluginType.HEADER):
            plugin.setConf(self.conf)
            if plugin.id == 'robots': #TODO: refactor
                plugin.setQueue(self.queue)
        elif plugin.category == PluginType.POSTPROCESS:
            plugin.setConf(self.conf)
            plugin.setDb(self.db)
        else:
            raise PluginTypeError


class TouchException(Exception):

    pass


class Transaction:

    def __init__(self, uri, depth, srcId, idno, method="GET", data=None):
        #Use the factory method below!!
        self.uri = uri
        self.aliases = [uri]
        self.depth = depth
        self.type = None
        self.file = None
        self.idno = idno
        self.srcId = srcId
        self.method = method
        self.data = data
        self.status = None
        self.cookies = None

    def changePrimaryUri(self, new_uri):
        self.aliases.append(new_uri)
        self.uri = new_uri

    def testLink(self, conf, journal, session):
        can = conf.regex_acceptor.canTouch(self.uri)
        if can:
            self.type, r = Network.check_link(self, journal, conf, session)
            return r
        else:
            raise TouchException()

    def loadResponse(self, conf, journal, session):
        try:
            acceptedTypes = self.getAcceptedTypes(conf)
            self.file = Network.getLink(self, acceptedTypes, conf, journal, session)
        except (NetworkError, ConditionError, StatusError):
            raise

    def getContent(self):
        with codecs.open(self.file, 'r', 'utf-8') as f:
            data = f.read()
            return str(data)

    def getStripedUri(self):
        pr = urlparse(self.uri)
        return str(pr.scheme+'://'+pr.netloc)

    def getAcceptedTypes(self, conf):
        if conf is None:
            return []
        else:
            return Transaction.__set2list(conf.type_acceptor.uris)


    def isWorthIt(self, conf):
        ra = conf.regex_acceptor.mightAccept(self.uri)
        return ra

    @staticmethod
    def __set2list(x):
        y = []
        for z in x:
          y.append(z)
        return y

transactionId = 0
def createTransaction(uri, depth = 0, parentId = -1, method = 'GET', params=dict()):
    assert (type(params) is dict) or (params is None)
    global transactionId
    decoded = str(urllib.parse.unquote(urllib.parse.unquote(uri)))
    tr = Transaction(decoded, depth, parentId, transactionId, method, params)
    transactionId = transactionId + 1
    return tr


class Rack:

    def __init__(self, typeAcceptor,regexAcceptor, plugins = []):

        self.plugins = plugins
        self.typeAcceptor = typeAcceptor
        self.regexAcceptor = regexAcceptor
        self.log = logging.getLogger(__name__)

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
        regex_cond = self.regexAcceptor.accept(transaction.uri, plugin.id)
        return type_cond and regex_cond

    def stop(self):
        pass

class TransactionQueue:


    def __init__(self, db, conf):
        self.__db = db
        self.__conf = conf
        self.__seen = set()
        self.__q = queue.Queue()
        
    def isEmpty(self):
        return self.__q.empty()

    def pop(self):
        try:
            t = self.__q.get(block=True, timeout=1)
            #t.uri.decode('utf-8')
        except queue.Empty:
            raise
        else:
            self.__db.log(Table.transactions, ('UPDATE transactions SET verificationStatus = ? WHERE id = ?', ["PROCESSING", t.idno]) )
            self.__db.log(Table.link_defect, ('UPDATE link SET processed = ? WHERE toUri = ?', [str("true"), str(t.uri)] ))
            return t

    def push(self, transaction, parent=None):

        #logging.getLogger(__name__).debug("Push link to "+transaction.uri)

        uri, params = TransactionQueue.__strip_parse_query(transaction)
        if (transaction.uri, transaction.method) in self.__conf.payloads: #chceme sem neco poslat
            params.update(self.__conf.payloads[(transaction.uri, transaction.method)])
            transaction.data = params
            transaction.uri = uri

        self.__mark_seen(transaction)

        if parent is not None:
            self.__db.log_link(parent.idno, transaction.uri, transaction.idno)

        self.__bake_cookies(transaction, parent)

    def push_link(self, uri, parent):
        if parent is None:
            self.push(createTransaction(uri, 0, -1), None)
        else:
            self.push(createTransaction(uri, parent.depth + 1, parent.idno), parent)

    def push_virtual_link(self, uri, parent):
        t = createTransaction(uri, parent.depth + 1, parent.idno)
        self.__mark_seen(t)
        self.__db.log_link(parent.idno, uri, t.idno)
        return t

    @staticmethod
    def __strip_parse_query(transaction):

         #strip query off uri and parse it into separate dict
        p = urlparse(transaction.uri)
        params = urllib.parse.parse_qs(p.query)
        p_ = ParseResult(p.scheme, p.netloc, p.path, p.params, None, None)
        uri = p_.geturl()

        return uri, params

    def __mark_seen(self, transaction):
        if (transaction.uri, transaction.method) not in self.__seen:
            self.__q.put(transaction)
            self.__db.log(Table.transactions,
                          ('INSERT INTO transactions (id, method, uri, origin, verificationStatus, depth) VALUES (?, ?, ?, \'CHECKER\', ?, ?)', 
                          [str(transaction.idno), transaction.method, transaction.uri, "REQUESTED", str(transaction.depth)]) )
            for uri in transaction.aliases:
                self.__db.log(Table.aliases,
                              ('INSERT INTO aliases (transactionId, uri) VALUES (?, ?)', [str(transaction.idno), uri]))
        #TODO: co kdyz jsme pristupovali s jinymi parametry?
        #mark all known aliases as seen
        for uri in transaction.aliases:
            if (uri, transaction.method) not in self.__seen:
                self.__seen.add( (transaction.uri, transaction.method) )


    def __bake_cookies(self, transaction, parent):
        cookies = dict()
        if parent is not None:
            cookies = parent.cookies.copy()
        allowed = False
        for reg in self.__conf.cookies:
            if reg.match(transaction.uri): #sending cookies allowed #TODO: aliases
                allowed = True
                # najit vsechna cookies pro danou adresu
                if reg in self.__conf.custom_cookies: #got custom cookies to send
                    cookies.update(self.__conf.custom_cookies[reg])
        if allowed:
            if len(cookies.keys()) > 0:
                logging.getLoggier(__name__).debug("Cookies of "+transaction.uri + " updated to " + str(cookies))
            transaction.cookies = cookies


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


    def __init__(self, db):
        self.__db = db
       
    def startChecking(self, transaction):
        logging.getLogger(__name__).debug("Starting checking " + transaction.uri)
        self.__db.log(Table.transactions, ('UPDATE transactions SET verificationStatus = ?, uri = ?, contentType = ?, responseStatus = ? WHERE id = ?', ["VERIFYING", transaction.uri, transaction.type, transaction.status, transaction.idno]) )

    def stopChecking(self, transaction, status):
        logging.getLogger(__name__).debug("Stopped checking " + transaction.uri)
        self.__db.log(Table.transactions, ('UPDATE transactions SET verificationStatus = ? WHERE id = ?', [str(status), transaction.idno]) )

    def foundDefect(self, transaction, defect, evidence, severity=0.5):
        self.foundDefect(transaction.idno, defect.name, defect.additional, evidence, severity)

    def foundDefect(self, trId, name, additional, evidence, severity = 0.5):
        assert type(trId) == int
        self.__db.log_defect(trId, name, additional, evidence, severity)

    def getKnownDefectTypes(self):
        return self.__db.get_known_defect_types()

    def gotCookie(self, transaction, name, value):
        self.__db.log_cookie(transaction.idno, name, value)

class Defect:


    def __init__(self, name, additional = None):
        self.name = name
        self.additional = additional

