import logging
import queue
import codecs
import datrie
import string
import urllib
from urllib.parse import urldefrag
from net import Network, NetworkError, ConditionError, StatusError
from database import Query
import sqlite3 as mdb


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

        if self.__conf.getProperty('loglink', True) and parent is not None:
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
        if self.__conf.getProperty('loglink', True):
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
