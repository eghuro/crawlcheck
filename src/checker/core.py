import logging
import queue
import urllib.parse
import os
import time
import copy
import codecs
import requests
from urllib.parse import urlparse, ParseResult, urldefrag
from database import DBAPI, VerificationStatus, Query
from common import PluginType, PluginTypeError
from net import Network, NetworkError, ConditionError, StatusError
from filter import FilterException, Reschedule
import gc
import sqlite3 as mdb
from rfc3987 import match
import datrie
import string


class Core:
    """ The core of the application. Main loop is implemented here."""

    def __init__(self, plugins, filters, headers, postprocess, conf):
        self.plugins = plugins
        self.log = logging.getLogger(__name__)
        self.conf = conf
        self.db = DBAPI(conf.dbconf)
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
        """ Run the checker. """
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

                if not match(transaction.uri):
                    self.log.error("Invalid URI: %s" % (transaction.uri))
                    self.journal.foundDefect(transaction.idno, "invaliduri",
                                             "URI is invalid",
                                             transaction.uri, 1.0)
                    self.journal.stopChecking(transaction,
                                              VerificationStatus.done_ko)
                    continue

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
            except Reschedule:  # eg. long crawl delay
                self.queue.push_rescheduled(transaction)
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
        self.log.info("Buffered: %s DB queries" %
                      (str(self.db.bufferedQueries)))
        self.log.info("Seen: %s addresses" % (str(self.queue.seenlen)))
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
        """ Run postprocessing. """

        self.log.info("Postprocessing")
        for pp in self.postprocessers:
            self.log.debug(pp.id)
            pp.process()

    def clean_tmps(self):
        """ Clean temporary files allocated by core. """

        for filename in self.files:
            try:
                os.remove(filename)
            except OSError:
                continue
            except TypeError:
                continue

    def clean(self):
        """ Cleanup. Clean temporary files and run garbage collection. """
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
    """ It is forbidden to touch the transaction (by configuration). """
    pass


class Transaction:
    """ Information about a web page is represented by this class."""

    def __init__(self, uri, depth, srcId, idno, method="GET", data=None):
        # Use the factory method below!!
        self.uri = uri
        self.aliases = set([uri])
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
        """Add a new alias and represent it as a primary URI."""
        uri = urldefrag(new_uri)[0]
        self.aliases.add(uri)
        self.uri = uri

    def testLink(self, conf, journal, session):
        """Phase 1 of downloading a page.
        Are we allowed (by configuration) to touch the link?
        If not, raise TouchException.
        Otherwise initiate the connection and return headers.
        """

        can = conf.regex_acceptor.canTouch(self.uri)
        if can:
            self.request = Network.testLink(self, journal, conf, session,
                                            self.getAcceptedTypes(conf))
            # nastavi status, type
            return self.request.headers
        else:
            raise TouchException()

    def loadResponse(self, conf, journal, session):
        """Phase 2 of downloading a page.
        Finish downloading by storing body into a temporary file.
        Errors are passed through.
        """

        try:
            Network.getContent(self, conf, journal)
            # pouzije request, nastavi file
        except (NetworkError, ConditionError, StatusError):
            raise

    def getContent(self):
        """Read content from underlying file as string."""
        try:
            with codecs.open(self.file, 'r', 'utf-8') as f:
                data = f.read()
                return str(data)
        except UnicodeDecodeError as e:
            logging.getLogger(__name__).error("Error loading content for %s" %
                                              self.uri)
            return ""

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


def createTransaction(uri, depth=0, parentId=-1, method='GET', params=dict(),
                      expected=None):
    """ Factory method for creating Transaction objects. """

    assert (type(params) is dict) or (params is None)
    global transactionId
    decoded = str(urllib.parse.unquote(urllib.parse.unquote(uri)))
    tr = Transaction(decoded, depth, parentId, transactionId, method, params)
    tr.expected = expected
    transactionId = transactionId + 1
    return tr


class Rack:
    """ Rack stores plugins.
    On run it passes the transaction to individual plugins.
    """
    def __init__(self, typeAcceptor, regexAcceptor, plugins=[]):
        self.plugins = plugins
        self.typeAcceptor = typeAcceptor
        self.regexAcceptor = regexAcceptor
        self.log = logging.getLogger(__name__)

    def run(self, transaction):
        """Let plugins handle the transaction one by one in a sequence."""

        for plugin in self.plugins:
            self.__run_one(transaction, plugin)
        transaction.cache = None

    def __run_one(self, transaction, plugin):
        if self.accept(transaction, plugin):
            self.log.info("%s started checking %s" %
                          (plugin.id, transaction.uri))
            plugin.check(transaction)
            self.log.debug("%s stopped checking %s" %
                           (plugin.id, transaction.uri))

    def accept(self, transaction, plugin):
        """Is the transaction accepted by the plugin?"""

        type_cond = self.typeAcceptor.accept(str(transaction.type), plugin.id)
        regex_cond = self.regexAcceptor.accept(transaction.uri, plugin.id)
        return type_cond and regex_cond


class SeenLimit(Exception):
    """ Reached a limit on amount of seen transactions. """
    pass


class TransactionQueue:
    """Transactons are stored here. Queue is stored locally. Operations are
    written through to database.
    """
    def __init__(self, db, conf):
        self.__db = db
        self.__conf = conf
        self.__seen = datrie.Trie(string.printable)
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
        """Push transaction into queue."""
        transaction.uri = urldefrag(transaction.uri)[0]

        try:
            self.__mark_seen(transaction)
        except SeenLimit:
            log.warn("Not logging link, because limit was reached")
            return

        if parent is not None:
            self.__db.log_link(parent.idno, transaction.uri, transaction.idno)

    def push_link(self, uri, parent, expected=None):
        """Push link into queue.
        Transactions are created, proper Referer header is set.
        """

        if parent is None:
            self.push(createTransaction(uri, 0, -1, 'GET', dict(), expected),
                      None)
        else:
            t = createTransaction(uri, parent.depth + 1, parent.idno, 'GET',
                                  dict(), expected)
            t.headers['Referer'] = parent.uri
            self.push(t, parent)

    def push_virtual_link(self, uri, parent):
        """Push virtual link into queue.
        Mark URI as seen, log link, write it all into DB.
        Doesn't push the queue.
        """

        t = createTransaction(uri, parent.depth + 1, parent.idno)
        self.__mark_seen(t)
        self.__db.log_link(parent.idno, uri, t.idno)
        return t

    def push_rescheduled(self, transaction):
        """Force put transaction into queue, no further checks.
        Transaction must've been seen previously.
        """
        assert self.__been_seen(transaction)
        self.__q.put(transaction)

    def __been_seen(self, transaction):
        if transaction.uri in self.__seen:
            return transaction.method in self.__seen[transaction.uri]
        return False

    def __set_seen(self, transaction):
        if transaction.uri in self.__seen:
            self.__seen[transaction.uri].add(transaction.method)
        else:
            self.__seen[transaction.uri] = set([transaction.method])

    def __record_params(self, transaction):
        if self.__conf.getProperty('recordParams', True):
            for key, value in transaction.data.items():
                self.__db.log_param(transaction.idno, key, value)

    def __test_url_limit(self):
        if self.__conf.getProperty('urlLimit') is not None:
            if self.seenlen >= self.__conf.getProperty('urlLimit'):
                raise SeenLimit()

    def __mark_seen(self, transaction):
        if not self.__been_seen(transaction):
            self.__test_url_limit()
            self.__q.put(transaction)
            self.__db.log(Query.transactions,
                          (str(transaction.idno), transaction.method,
                           transaction.uri, "REQUESTED",
                           str(transaction.depth), str(transaction.expected)))
            for uri in transaction.aliases:
                self.__db.log(Query.aliases, (str(transaction.idno), uri))
            self.__record_params(transaction)
        # co kdyz jsme pristupovali s jinymi parametry?
        # mark all known aliases as seen
        for uri in transaction.aliases:
            if not self.__been_seen(transaction):
                self.__set_seen(transaction)
                self.seenlen = self.seenlen + 1


class Journal:
    """Journal logs events and writes them through to the DB."""

    def __init__(self, db, conf):
        self.__db = db
        self.__conf = conf

    def startChecking(self, transaction):
        """Change status as we've started checking a transaction.
        Also store headers if needed.
        """

        logging.getLogger(__name__).debug("Starting checking %s" %
                                          (transaction.uri))
        self.__db.log(Query.transactions_load,
                      ("VERIFYING", transaction.uri, transaction.type,
                       transaction.status, transaction.idno))

        # zapsat ziskane hlavicky
        if self.__conf.getProperty('recordHeaders', True):
            for key, value in transaction.headers.items():
                self.__db.log_header(transaction.idno, key, value)

    def stopChecking(self, transaction, status):
        """Update status as we've stopped checking a transaction.
        """

        logging.getLogger(__name__).debug("Stopped checking %s" %
                                          (transaction.uri))
        self.__db.log(Query.transactions_status,
                      (str(status), transaction.idno))

    def foundDefect(self, transaction, defect, evidence, severity=0.5):
        """Log a defect."""
        self.foundDefect(transaction.idno, defect.name, defect.additional,
                         evidence, severity)

    def foundDefect(self, trId, name, additional, evidence, severity=0.5):
        """Log a defect."""
        assert type(trId) == int
        self.__db.log_defect(trId, name, additional, evidence, severity)

    def getKnownDefectTypes(self):
        """Get currently known defect types."""
        with mdb.connect(self.__conf.dbconf.getDbname()) as con:
            return self.__db.get_known_defect_types(con)

    def gotCookie(self, transaction, name, value, secure, httpOnly, path):
        """Log a discovered cookie."""
        self.__db.log_cookie(transaction.idno, name, value, secure, httpOnly,
                             path)


class Defect:

    def __init__(self, name, additional=None):
        self.name = name
        self.additional = additional
