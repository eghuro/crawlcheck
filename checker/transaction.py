import logging
import queue
import codecs
import datrie
import string
import urllib
from urllib.parse import urldefrag
import copy
import json
import redis
from cachetools import cached, LRUCache
try:
    from .net import Network, NetworkError, ConditionError, StatusError
except ImportError:
    from net import Network, NetworkError, ConditionError, StatusError


class TouchException(Exception):
    """ It is forbidden to touch the transaction (by configuration). """
    pass


class Transaction:
    """ Information about a web page is represented by this class."""

    def __init__(self, conf, uri, depth, srcId, idno, method="GET", data=None, size=0):
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
        self.size = size
        self.status = None
        self.cookies = None
        self.request = None
        self.expected = None
        self.headers = dict()
        self.cache = None
        self.conf = conf

    @staticmethod
    def from_json(jsn, conf):
        jsn = json.loads(jsn)
        t = Transaction(conf, jsn['uri'], jsn['depth'], jsn['srcId'], jsn['idno'], jsn['method'], jsn['data'], len(jsn['data']))
        t.aliases = set(jsn['aliases'])
        t.type = jsn['type']
        t.file = jsn['file']
        t.status = jsn['status']
        t.cookies = jsn['cookies']
        t.expected = jsn['expected']
        t.headers = jsn['headers']
        return t

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

    @cached(LRUCache(maxsize=1))
    def getContent(self):
        """Read content from underlying file as string."""
        try:
            r = redis.StrictRedis(host=self.conf.getProperty('redisHost', 'localhost'),
                                  port=self.conf.getProperty('redisPort', 6379),
                                  db=self.conf.getProperty('redisDb', 0))
            return r.get(self.file)
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


def createTransaction(red, conf, uri, depth=0, parentId=-1, method='GET', params=dict(),
                      expected=None):
    """ Factory method for creating Transaction objects. """

    assert (type(params) is dict) or (params is None)
    decoded = str(urllib.parse.unquote(urllib.parse.unquote(uri)))
    transactionId = red.incr("transactionId")
    tr = Transaction(conf, decoded, depth, parentId, transactionId, method, params)
    tr.expected = expected
    return tr


class SeenLimit(Exception):
    """ Reached a limit on amount of seen transactions. """
    pass


class RedisTransactionQueue:
    """Transactons are stored here. Queue is stored locally. Operations are
    written through to database.
    """
    def __init__(self, db, conf):
        self.__db = db
        self.__conf = conf
        self.__redis = redis.StrictRedis(host=conf.getProperty('redisHost', 'localhost'), port=conf.getProperty('redisPort', 6379), db=conf.getProperty('redisDb', 0))
        self.__log = logging.getLogger(__name__)

    def isEmpty(self):
        return self.len() == 0

    def len(self):
        return self.__redis.llen('transactions' + self.__conf.getProperty('runIdentifier'))

    def pop(self):
        x = self.__redis.rpop('transactions' + self.__conf.getProperty('runIdentifier')).decode('utf-8')
        if x == None:
            return None
        self.__log.debug(str(x))

        t = Transaction.from_json(x, self.__conf)
        return t

    def push(self, transaction, parent=None):
        """Push transaction into queue."""
        transaction.uri = urldefrag(transaction.uri)[0]

        cnt = 0
        trId = transaction.idno
        for uri in transaction.aliases:
            if 0 == self.__redis.pfadd('seen' + self.__conf.getProperty('runIdentifier'), uri):
                if uri is not transaction.uri:
                    self.__log.warn("Transaction id " + str(transaction.idno) + " was previously seen under different alias: " + uri +".\nTransaction URI: " + transaction.uri +"\nAliases:\n"+ "\n".join(transaction.aliases))
                iden = self.__redis.hget('transactionId' + self.__conf.getProperty('runIdentifier'), uri)
                if iden is not None:
                    trId = int(iden.decode('utf-8'))
                    self.__log.debug("Using transaction id: " + str(trId) + " for " + uri + "(was: " + str(transaction.idno) + ")")
                    break
                else:
                    self.__log.warn("Previous transaction ID was not recorded for " + uri + " (transaction id: " + str(trId) + ")")
                    cnt = cnt + 1
            else:
                cnt = cnt + 1

        #cnt je pocet novych aliasu
        if cnt == len(transaction.aliases): #vsechny aliasy nove -> stranku vidime prvne
            self.__db.log_transaction(transaction.idno, transaction.method, transaction.uri, transaction.depth, transaction.expected, transaction.aliases)
            self.__record_params(transaction)
            self.__enqueue(transaction)
            for alias in transaction.aliases:
                self.__redis.hset('transactionId' + self.__conf.getProperty('runIdentifier'), alias, str(transaction.idno))

        if self.__conf.getProperty('loglink', True) and parent is not None:
            if 1 == self.__redis.sadd('links' + self.__conf.getProperty('runIdentifier'), str(parent.idno) + ';' + str(trId)):
                self.__db.log_link(parent.idno, transaction.uri, trId) # trId je bud transaction.idno a stranku jsme logovali nebo jine, "primarni id" stranky

    def push_link(self, uri, parent, expected=None):
        """Push link into queue.
        Transactions are created, proper Referer header is set.
        """

        if parent is None:
            self.push(createTransaction(self.__redis, self.__conf, uri, 0, -1, 'GET', dict(), expected),
                      None)
        else:
            t = createTransaction(self.__redis, self.__conf, uri, parent.depth + 1, parent.idno, 'GET',
                                  dict(), expected)
            t.headers['Referer'] = parent.uri
            self.push(t, parent)

    def push_virtual_link(self, uri, parent):
        """Push virtual link into queue.
        Mark URI as seen, log link, write it all into DB.
        Doesn't push the queue.
        """

        t = createTransaction(self.__redis, self.__conf, uri, parent.depth + 1, parent.idno)
        self.__redis.pfadd('seen' + self.__conf.getProperty('runIdentifier'), t.uri)
        if self.__conf.getProperty('loglink', True):
            self.__db.log_link(parent.idno, uri, t.idno)
        return t

    def push_entrypoint(self, entryPoint):
        t = createTransaction(self.__redis, self.__conf,
                              entryPoint.url, 0, -1,
                              entryPoint.method, entryPoint.data)
        self.push(t, None)

    def push_rescheduled(self, transaction):
        """Force put transaction into queue, no further checks.
        Transaction must've been seen previously.
        """
        assert self.__redis.pfcount('seen' + self.__conf.getProperty('runIdentifier'), transaction.uri) > 0
        self.__enqueue(transaction)

    def __enqueue(self, transaction):
        conf = transaction.conf
        transaction.conf = None
        tr = copy.deepcopy(transaction)
        tr.aliases = list(tr.aliases)
        transaction.conf = conf
        self.__redis.lpush("transactions" + self.__conf.getProperty('runIdentifier'), json.dumps(tr.__dict__).encode('utf8'))

    def __record_params(self, transaction):
        if self.__conf.getProperty('recordParams', True):
            for key, value in transaction.data.items():
                self.__db.log_param(transaction.idno, key, value)


class Journal:
    """Journal logs events and writes them through to the DB."""

    def __init__(self, db, conf, defectTypes):
        self.__db = db
        self.__conf = conf
        self.__defTyp = defectTypes

    def startChecking(self, transaction):
        """Change status as we've started checking a transaction.
        Also store headers if needed.
        """

        logging.getLogger(__name__).debug("Starting checking %s" %
                                          (transaction.uri))
        # zapsat ziskane hlavicky
        if self.__conf.getProperty('recordHeaders', True):
            for key, value in transaction.headers.items():
                self.__db.log_header(transaction.idno, key, value)

    def stopChecking(self, transaction, status):
        """Update status as we've stopped checking a transaction.
        """

        logging.getLogger(__name__).debug("Stopped checking %s" %
                                          (transaction.uri))
        self.__db.session.commit()
        self.__db.log_transaction_data(transaction.idno, transaction.status, transaction.type, transaction.size, status)

    def getKnownDefectTypes(self):
        """Get currently known defect types."""
        return self.__defTyp

    def foundDefect(self, transaction, defect, evidence, severity=0.5):
        """Log a defect."""
        self.foundDefect(transaction.idno, defect.name, defect.additional,
                         evidence, severity)

    def foundDefect(self, trId, name, additional, evidence, severity=0.5):
        """Log a defect."""
        assert type(trId) == int
        self.__db.log_defect(trId, name, additional, evidence, severity)


    def gotCookie(self, transaction, name, value, secure, httpOnly, path):
        """Log a discovered cookie."""
        self.__db.log_cookie(transaction.idno, name, value, secure, httpOnly,
                             path)


class Defect:

    def __init__(self, name, additional=None):
        self.name = name
        self.additional = additional
