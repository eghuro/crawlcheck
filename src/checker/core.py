import logging
import queue
import urllib.parse
import os
import time
import copy
import codecs
import requests
from urllib.parse import urlparse, ParseResult
from pluginDBAPI import DBAPI, VerificationStatus, Query
from common import PluginType, PluginTypeError
from net import Network, NetworkError, ConditionError, StatusError
from filter import FilterException
import gc
import sqlite3 as mdb


class Core:

    def __init__(self, plugins, filters, headers, postprocess, conf):
        self.plugins = plugins
        self.log = logging.getLogger(__name__)
        self.conf = conf
        self.db = DBAPI(conf.dbconf)
        with mdb.connect(conf.dbconf.getDbname()) as con:
            self.db.load_defect_types(con)
            self.db.load_finding_id(con)
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

        self.journal = Journal(self.db, self.conf)

        for plugin in self.plugins+headers+filters+postprocess:
            self.__initializePlugin(plugin)

        self.__push_entry_points()
        self.rack = Rack(self.conf.type_acceptor, self.conf.regex_acceptor,
                         plugins)

    def __push_entry_points(self):
        for entryPoint in self.conf.entry_points:
            self.log.debug("Pushing to queue: %s, data: %s" %
                           (entryPoint.url, str(entryPoint.data)))
            self.queue.push(createTransaction(entryPoint.url, 0, -1,
                                              entryPoint.method,
                                              entryPoint.data))

    def run(self):
        with requests.Session() as session:
            self.__run(session)

    def __handle_err(self, msg, transaction,
                     status=VerificationStatus.done_ignored):
        self.log.debug(msg)
        self.files.append(transaction.file)
        self.journal.stopChecking(transaction, status)

    def __filter(self, transaction, session):
        # Custom filters: depth, robots.txt
        for tf in self.filters:
            tf.filter(transaction)

        start = time.time()
        r = transaction.testLink(self.conf, self.journal, session)
        # precte hlavicky

        # custom HTTP header filters, incl. test if ct matches expectation
        for hf in self.header_filters:
            hf.filter(transaction, r)

        return start

    def __run(self, session):
        # Queue
        while not self.queue.isEmpty():
            try:
                transaction = self.queue.pop()
            except queue.Empty:
                continue

            try:
                if type(transaction.uri) != str:
                    transaction.uri = str(transaction.uri)

                self.log.info("Processing %s" % (transaction.uri))

                if not transaction.isWorthIt(self.conf):
                    # neni zadny plugin, ktery by prijal
                    self.log.debug("%s not worth my time" % (transaction.uri))
                    self.journal.stopChecking(transaction,
                                              VerificationStatus.done_ignored)
                    continue

                start = self.__filter(transaction, session)
                transaction.loadResponse(self.conf, self.journal, session)
                # precte telo
            except TouchException:  # nesmim se toho dotykat
                self.__handle_err("Forbidden to touch %s" %
                                  (transaction.uri), transaction)
                continue
            except ConditionError:  # URI nebo content-type dle konfigurace
                self.__handle_err("Condition failed", transaction)
                continue
            except FilterException:  # filters
                self.__handle_err("%s filtered out" % (transaction.uri),
                                  transaction)
                continue
            except StatusError as e:  # already logged
                self.journal.stopChecking(transaction,
                                          VerificationStatus.done_ko)
                self.files.append(transaction.file)
                continue
            except NetworkError as e:
                self.__handle_err("Network error: %s" % (format(e)),
                                  transaction, VerificationStatus.done_ko)
                continue
            else:  # Plugins
                self.__process(transaction, start)

    def __process(self, transaction, start):
        for sub in self.__time_subscribers:
            sub.markStart(start, transaction.uri)
        self.files.append(transaction.file)
        transaction.cache = dict()
        transaction.cache['size'] = os.path.getsize(transaction.file)
        self.volume = self.volume + transaction.cache['size']
        self.journal.startChecking(transaction)
        self.rack.run(transaction)
        self.journal.stopChecking(transaction, VerificationStatus.done_ok)
        if self.volume > self.conf.getProperty("maxVolume"):
            # call cleanup only if there are files to remove
            # ensures gc.collect() is called once in a while but not often
            self.__cleanup()

    def __cleanup(self):
        while self.volume > (self.conf.getProperty("maxVolume") / 2):
            self.log.debug("CLEANUP ... Size of tmps: %s, limit: %s" %
                           (str(self.volume),
                            str(self.conf.getProperty("maxVolume"))))
            f = self.files[0]
            if f:
                l = os.path.getsize(f)
                os.remove(f)
                self.volume = self.volume - l
            self.files.pop(0)
        self.log.debug("Size of tmps after cleanup: %s" % (str(self.volume)))
        self.log.info("Enqueued: %s transactions" % (str(self.queue.len())))
        self.log.info("Buffered: %s DB queries" % (str(self.db.bufferedQueries)))
        self.log.info("Seen: % addresses" % (str(self.queue.seenlen)))
        gc.collect()

    def finalize(self):
        self.log.debug("Finalizing")
        try:
            # write to database
            self.db.sync(final=True)
        except:
            self.log.exception("Unexpected exception while syncing")
        finally:
            # clean tmp files and queue & list of seen addresses
            self.clean()
            # run postprocessing
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
            except TypeError:
                continue

    def clean(self):
        self.clean_tmps()
        self.__queue = None
        gc.collect()

    def __initializePlugin(self, plugin):
        plugin.setJournal(self.journal)
        known_categories = set([PluginType.CRAWLER, PluginType.CHECKER,
                                PluginType.FILTER, PluginType.HEADER,
                                PluginType.POSTPROCESS])

        if plugin.category not in known_categories:
            raise PluginTypeError

        try:
            plugin.setQueue(self.queue)
        except AttributeError:
            pass

        if plugin.category in set([PluginType.FILTER, PluginType.HEADER,
                                   PluginType.POSTPROCESS]):
            plugin.setConf(self.conf)
            if plugin.category == PluginType.POSTPROCESS:
                plugin.setDb(self.db)


class TouchException(Exception):

    pass


class Transaction:

    def __init__(self, uri, depth, srcId, idno, method="GET", data=None):
        # Use the factory method below!!
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
        self.request = None
        self.expected = None
        self.headers = dict()
        self.cache = None

    def changePrimaryUri(self, new_uri):
        self.aliases.append(new_uri)
        self.uri = new_uri

    def testLink(self, conf, journal, session):
        can = conf.regex_acceptor.canTouch(self.uri)
        if can:
            self.request = Network.testLink(self, journal, conf, session,
                                            self.getAcceptedTypes(conf))
            # nastavi status, type
            return self.request.headers
        else:
            raise TouchException()

    def loadResponse(self, conf, journal, session):
        try:
            Network.getContent(self, conf, journal)
            # pouzije request, nastavi file
        except (NetworkError, ConditionError, StatusError):
            raise

    def getContent(self):
        try:
            with codecs.open(self.file, 'r', 'utf-8') as f:
                data = f.read()
                return str(data)
        except UnicodeDecodeError as e:
            logging.getLogger(__name__).error("Error loading content for %s" %
                                              self.uri)
            return ""

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


def createTransaction(uri, depth=0, parentId=-1, method='GET', params=dict()):
    assert (type(params) is dict) or (params is None)
    global transactionId
    decoded = str(urllib.parse.unquote(urllib.parse.unquote(uri)))
    tr = Transaction(decoded, depth, parentId, transactionId, method, params)
    transactionId = transactionId + 1
    return tr


class Rack:

    def __init__(self, typeAcceptor, regexAcceptor, plugins=[]):
        self.plugins = plugins
        self.typeAcceptor = typeAcceptor
        self.regexAcceptor = regexAcceptor
        self.log = logging.getLogger(__name__)

    def run(self, transaction):
        for plugin in self.plugins:
            self.__run_one(transaction, plugin)
        transaction.cache = None

    def __run_one(self, transaction, plugin):
        if self.accept(transaction, plugin):
            self.log.info("%s started checking %s" %
                          (plugin.id, transaction.uri))
            plugin.check(transaction)
            self.log.info("%s stopped checking %s" %
                          (plugin.id, transaction.uri))

    def accept(self, transaction, plugin):
        rot = transaction.getStripedUri()[::-1]
        type_cond = self.typeAcceptor.accept(str(transaction.type), plugin.id)
        regex_cond = self.regexAcceptor.accept(transaction.uri, plugin.id)
        return type_cond and regex_cond


class TransactionQueue:

    def __init__(self, db, conf):
        self.__db = db
        self.__conf = conf
        self.__seen = set()
        self.__q = queue.Queue()
        self.seenlen = 0

    def isEmpty(self):
        return self.__q.empty()

    def len(self):
        return self.__q.qsize()

    def pop(self):
        try:
            t = self.__q.get(block=True, timeout=1)
        except queue.Empty:
            raise
        else:
            self.__db.log(Query.transactions_status, ("PROCESSING", t.idno))
            self.__db.log(Query.link_status, (str("true"), str(t.uri)))
            return t

    def push(self, transaction, parent=None):
        uri, params = TransactionQueue.__strip_parse_query(transaction)
        if (transaction.uri, transaction.method) in self.__conf.payloads:
            # chceme sem neco poslat
            params.update(self.__conf.payloads[(transaction.uri,
                                                transaction.method)])
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
            t = createTransaction(uri, parent.depth + 1, parent.idno)
            t.headers['Referer'] = parent.uri
            self.push(t, parent)

    def push_virtual_link(self, uri, parent):
        t = createTransaction(uri, parent.depth + 1, parent.idno)
        self.__mark_seen(t)
        self.__bake_cookies(t, parent)
        self.__db.log_link(parent.idno, uri, t.idno)
        return t

    @staticmethod
    def __strip_parse_query(transaction):
        # strip query off uri and parse it into separate dict
        p = urlparse(transaction.uri)
        params = urllib.parse.parse_qs(p.query)
        p_ = ParseResult(p.scheme, p.netloc, p.path, p.params, None, None)
        uri = p_.geturl()

        return uri, params

    def __mark_seen(self, transaction):
        if (transaction.uri, transaction.method) not in self.__seen:
            self.__q.put(transaction)
            self.__db.log(Query.transactions,
                          (str(transaction.idno), transaction.method,
                           transaction.uri, "REQUESTED",
                           str(transaction.depth)))
            for uri in transaction.aliases:
                self.__db.log(Query.aliases, (str(transaction.idno), uri))
        # TODO: co kdyz jsme pristupovali s jinymi parametry?
        # mark all known aliases as seen
        for uri in transaction.aliases:
            if (uri, transaction.method) not in self.__seen:
                self.__seen.add((transaction.uri, transaction.method))
                self.seenlen = self.seenlen + 1

    def __init_cookies(self, parent):
        if parent and parent.cookies:
            return parent.cookies.copy()
        else:
            return dict()

    def __bake_cookies(self, transaction, parent):
        cookies = self.__init_cookies(parent)
        allowed = False
        for reg in self.__conf.cookies:
            if reg.match(transaction.uri):  # sending cookies allowed
                # TODO: aliases
                allowed = True
                # najit vsechna cookies pro danou adresu
                if reg in self.__conf.custom_cookies:
                    # got custom cookies to send
                    cookies.update(self.__conf.custom_cookies[reg])
        if allowed:
            transaction.cookies = cookies

    def load(self):
        with mdb.connect(self.__conf.dbconf.getDbname()) as con:
            # load transactions from DB to memory
            # only where status is requested
            for t in self.__db.get_requested_transactions(con):
                # uri = t[0]; depth = t[1]; idno = t[3]
                srcId = -1
                if t[2] is not None:
                    srcId = t[2]
                decoded = str(urllib.parse.unquote(urllib.parse.unquote(t[0])),
                              'utf-8')
                self.__q.put(Transaction(decoded, t[1], srcId, t[3]))
            # load uris from transactions table for list of seen URIs
            self.__seen.update(self.__db.get_seen_uris(con))
            # set up transaction id for factory method
            transactionId = self.__db.get_max_transaction_id(con) + 1


class Journal:

    def __init__(self, db, conf):
        self.__db = db
        self.__conf = conf

    def startChecking(self, transaction):
        logging.getLogger(__name__).debug("Starting checking %s" %
                                          (transaction.uri))
        self.__db.log(Query.transactions_load,
                      ("VERIFYING", transaction.uri, transaction.type,
                       transaction.status, transaction.idno))

    def stopChecking(self, transaction, status):
        logging.getLogger(__name__).debug("Stopped checking %s" %
                                          (transaction.uri))
        self.__db.log(Query.transactions_status,
                      (str(status), transaction.idno))

    def foundDefect(self, transaction, defect, evidence, severity=0.5):
        self.foundDefect(transaction.idno, defect.name, defect.additional,
                         evidence, severity)

    def foundDefect(self, trId, name, additional, evidence, severity=0.5):
        assert type(trId) == int
        self.__db.log_defect(trId, name, additional, evidence, severity)

    def getKnownDefectTypes(self):
        with mdb.connect(self.__conf.dbconf.getDbname()) as con:
            return self.__db.get_known_defect_types(con)

    def gotCookie(self, transaction, name, value):
        self.__db.log_cookie(transaction.idno, name, value)


class Defect:

    def __init__(self, name, additional=None):
        self.name = name
        self.additional = additional
