from net import Network, NetworkError, ConditionError, StatusError
import codecs
import urllib.parse
import queue
import logging
from pluginDBAPI import Table
from urllib.parse import urlparse, ParseResult


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
        self.status = None
        self.cookies = None

    def testLink(self, conf, journal):
        if conf.uri_acceptor.canTouch(self.uri) or conf.suffix_acceptor.canTouch(self.getStripedUri()[::-1]) or conf.regex_acceptor.canTouch(self.uri):
            self.type, r = Network.check_link(self, journal, conf)
            return r
        else:
            raise TouchException()

    def loadResponse(self, conf, journal):
        try:
            acceptedTypes = self.getAcceptedTypes(conf)
            self.file = Network.getLink(self, acceptedTypes, conf, journal)
        except (NetworkError, ConditionError, StatusError):
            raise

    def getContent(self):
        with codecs.open(self.file, 'r', 'utf-8') as f:
            data = f.read()
            return str(data)

    def getStripedUri(self):
        pr = urlparse(self.uri)
        return str(pr.scheme+'://'+pr.netloc)

    def __get_accepted_types(self, uriMap, uriAcceptor):
        p = uriAcceptor.getMaxPrefix(self.uri)
        if p in uriMap:
            if uriMap[p]:
                return set(uriMap[p])
        return {}
 

    def getAcceptedTypes(self, conf):
        if conf is None:
            return []
        
        if conf.uri_map is None:
            acceptedTypes = {}
        else:
            acceptedTypes = self.__get_accepted_types(conf.uri_map, conf.uri_acceptor)
        
        bak = self.uri
        self.uri = self.uri[::-1]
        if conf.suffix_uri_map is not None:
             acceptedTypes += self.__get_accepted_types(conf.suffix_uri_map, conf.suffix_acceptor)
        self.uri = bak
        return self.__set2list(acceptedTypes)

    def isWorthIt(self, conf):
        ua = conf.uri_acceptor.mightAccept(self.uri)
        sa = conf.suffix_acceptor.mightAccept(self.getStripedUri()[::-1])
        ra = conf.regex_acceptor.mightAccept(self.uri)
        return ua or sa or ra

    @staticmethod
    def __set2list(x):
        y = []
        for z in x:
          y.append(z)
        return y

#transactionId = 0
#must be locked as if accessing queue
def createTransaction(uri, depth = 0, parentId = -1, method = 'GET', params=dict()):
    log = logging.getLogger()
    assert (type(params) is dict) or (params is None)
    #global transactionId
    decoded = str(urllib.parse.unquote(urllib.parse.unquote(uri)))
    tr = Transaction(decoded, depth, parentId, TransactionQueue.getTransactionId(), method, params)
    return tr

class TransactionQueue:


    __transactionId = -1
    status_ids = dict()
    
    @staticmethod
    def initialize():
        TransactionQueue.status_ids["requested"] = 1
        TransactionQueue.status_ids["processing"] = 2

    @staticmethod
    def getTransactionId():
        TransactionQueue.__transactionId = TransactionQueue.__transactionId + 1
        return TransactionQueue.__transactionId

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
            self.__db.log_process_link(TransactionQueue.status_ids["processing"], t.idno, t.uri)
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
            self.push(createTransaction(uri,parent.depth+1, parent.idno), parent)

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
            self.__seen.add( (transaction.uri, transaction.method) )
            self.__q.put(transaction)
            self.__db.log_seen(transaction, TransactionQueue.status_ids["requested"])
        #TODO: co kdyz jsme pristupovali s jinymi parametry?

    def __bake_cookies(self, transaction, parent):
        if self.__conf.uri_acceptor.getMaxPrefix(transaction.uri) in self.__conf.cookies: #sending cookies allowed
            cookies = dict()
            #najit vsechna cookies pro danou adresu
            if parent is not None:
                if parent.cookies is not None:
                    cookies = parent.cookies.copy()
            if self.__conf.uri_acceptor.getMaxPrefix(transaction.uri) in self.__conf.custom_cookies: #got custom cookies to send
                cookies.update(self.__conf.custom_cookies[self.__conf.uri_acceptor.getMaxPrefix(transaction.uri)])
            if len(cookies.keys()) > 0:
                logging.getLogger(__name__).debug("Cookies of "+transaction.uri+" updated to "+str(cookies))
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
