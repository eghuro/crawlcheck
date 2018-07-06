"""Database connector.
To access the database an API is provided.
Configuration is represented by DatabaseConfiguration object.
Class DBAPI represents the database API.
"""

import sqlite3 as mdb
from enum import Enum, IntEnum
import logging
import gc
from multiprocessing import Process, Queue, Pool
from functools import partial
import copy
import json
import redis


class DatabaseConfiguration(object):
    """ Configuration class for DBAPI.

    Configuration is set through respective setters and read through getters.

    Attributes:
        dbname (str): Sqlite3 database file to use
    """

    def __init__(self):
        """Default constructor.
        """

        self.__dbname = ""
        self.__limit = 0

    def getDbname(self):
        """ Database name getter.
        """

        return self.__dbname

    def setDbname(self, dbname):
        """Database name setter.

        Args:
            dbname: database name where data are stored
        """

        self.__dbname = dbname

    def getLimit(self):
        return self.__limit

    def setLimit(self, limit):
        self.__limit = limit


class VerificationStatus(Enum):
    requested = "REQUESTED"
    done_ok = "DONE - OK"
    done_ko = "DONE - KO"
    done_ignored = "DONE - IGNORED"


class Query(IntEnum):
    transactions = 1
    link = 2
    defect = 5
    defect_types = 3
    aliases = 4
    cookies = 6
    transactions_load = 7
    transactions_status = 8
    link_status = 0
    headers = 9
    params = 10


class DBAPI(object):
    """ API for access to the underlying database.
    """

    query_types = [Query.defect_types, Query.transactions,
                   Query.transactions_load, Query.transactions_status,
                   Query.aliases,  Query.link, Query.link_status,
                   Query.defect, Query.cookies, Query.headers,
                   Query.params]

    queries = { Query.link: ('INSERT INTO link (findingId, toUri, '
                             'requestId, responseId) VALUES (?,?,?,?)'),
                Query.defect_types: ('INSERT INTO defectType (id, type,'
                                     'description) VALUES (?, ?, ?)'),
                Query.defect: ('INSERT INTO defect (findingId, type, '
                               'evidence, severity, responseId) VALUES '
                               '(?, ?, ?, ?, ?)'),
                Query.cookies: ('INSERT INTO cookies (findingId, '
                                'name, value, responseId, secure, '
                                'httpOnly, path) VALUES (?, ?, ?, ?, '
                                '?, ?, ?)'),
                Query.aliases: ('INSERT INTO aliases (transactionId, '
                                'uri) VALUES (?, ?)'),
                Query.transactions: ('INSERT INTO transactions (id, '
                                     'method, uri, verificationStatus,'
                                     'depth, expected) VALUES '
                                     '(?, ?, ?, ?, ?, ?)'),
                Query.transactions_load: ('UPDATE transactions SET '
                                          'verificationStatus = ?, '
                                          'uri = ?, contentType = ?, '
                                          'responseStatus = ? WHERE '
                                          'id = ?'),
                Query.transactions_status: ('UPDATE transactions SET '
                                            'verificationStatus = ? '
                                            'WHERE id = ?'),
                Query.link_status: ('UPDATE link SET processed = ? '
                                    'WHERE toUri = ?'),
                Query.headers: ('INSERT INTO headers (findingId, '
                                'name, value, responseId) VALUES (?, ?,'
                                ' ?, ?)'),
                Query.params: ('INSERT into param (findingId, '
                               'responseId, key, value) VALUES (?, ?, '
                               '?, ?)')
    }

    __KEY_BASE = "dblogbuf"


    def __init__(self, conf):
        self.__redis = redis.StrictRedis(host=conf.getProperty('redisHost', 'localhost'),
                                         port=conf.getProperty('redisPort', 6379),
                                         db=conf.getProperty('redisDb', 0))
        self.__conf = conf
        self.conf = conf.dbconf
        self.limit = self.conf.getLimit()
        self.__syncer_worker = None
        self.__sync_cnt = 0

    def log(self, query, query_params):
        """Log a query."""
        key = DBAPI.__KEY_BASE + str(int(query))
        self.__redis.lpush(key, json.dumps(query_params))

        qcount = sum(self.__redis.llen(DBAPI.__KEY_BASE + str(int(qt))) for qt in self.query_types)

        if qcount > self.limit:
            self.sync()
            gc.collect()

    def log_link(self, parent_id, uri, new_id):
        """Log link from parent_id to uri with new_id."""
        fid = self.__redis.incr("findingId")
        self.log(Query.link,
                 (str(fid), uri, str(new_id), str(parent_id)))

    def log_defect(self, transactionId, name, additional, evidence,
                   severity=0.5):
        """Log a defect."""
        fid = self.__redis.incr("findingId")
        if self.__redis.hexists("defectType", name) == 1:
            did = self.__redis.hget("defectType", name)
        else:
            did = self.__redis.incr("defectId")
            self.__redis.hset("defectType", name, did)
            self.log(Query.defect_types, (str(did), str(name), str(additional)))

        self.log(Query.defect,
                 (str(fid), str(did), str(evidence), str(severity), str(transactionId)))

    def log_cookie(self, transactionId, name, value, secure, httpOnly, path):
        """Log a cookie."""
        fid = self.__redis.incr("findingId")
        self.log(Query.cookies,
                 (str(fid), str(name), str(value),
                  str(transactionId), str(secure), str(httpOnly), str(path)))

    def log_header(self, transactionId, name, value):
        """ Log a header. """
        fid = self.__redis.incr("findingId")
        self.log(Query.headers,
                 (str(fid), str(name), str(value), str(transactionId)))

    def log_param(self, transactionId, key, value):
        """ Log an URI parameter. """
        fid = self.__redis.incr("findingId")
        self.log(Query.param, (str(fid), str(transactionId), key, value))

    @staticmethod
    def syncer(conf, dbname, qtypes, vacuum=True):
        """Sync records into DB. Worker."""
        log = logging.getLogger(__name__)
        log.info("Writing into database")
        red = redis.StrictRedis(host=conf.getProperty('redisHost', 'localhost'),
                                port=conf.getProperty('redisPort', 6379),
                                db=conf.getProperty('redisDb', 0))
        with mdb.connect(dbname) as con, red.pipeline() as pipe:
            try:
                cursor = con.cursor()

                cursor.execute("PRAGMA synchronous = OFF")
                cursor.execute("PRAGMA page_size = 65536")
                cursor.execute("PRAGMA journal_mode = MEMORY")
                cursor.execute("PRAGMA auto_vacuum = NONE")

                # https://www.sqlite.org/pragma.html#pragma_page_size

                for qtype in qtypes:
                    key = "dbbuf" + str(int(qtype))
                    log.debug("Query: %s, key: %s" % (str(qtype), key))
                    cursor.executemany(DBAPI.queries[qtype], [json.loads(x) for x in red.lrange(key, 0, -1)])
                    pipe.delete(key)

                con.commit()

                if vacuum:
                    log.debug("Vacuum")
                    cursor.execute("VACUUM")

            except mdb.Error as e:
                con.rollback()
                log.error("SQL Error: "+str(e))
            else:
                pipe.execute()
                log.info("Sync successful")

    def sync(self, final=False):
        """ Actually write cached queries into the database. """
        log = logging.getLogger(__name__)
        log.info("Syncing database")
        if self.__syncer_worker:
            log.info("Waiting for DB sync worker to finish")
            self.__syncer_worker.join()

        vacuum = (self.__sync_cnt % 100 == 0)
        for qtype in self.query_types:
            oldKey = DBAPI.__KEY_BASE + str(int(qtype))
            newKey = "dbbuf" + str(int(qtype))
            if self.__redis.exists(oldKey) == 1:
                self.__redis.rename(oldKey, newKey)

        sproc = Process(name="DB sync worker",
                        target=DBAPI.syncer, args=(self.__conf, self.conf.getDbname(),
                                                   DBAPI.query_types,
                                                   vacuum))
        self.__syncer_worker = sproc
        sproc.start()
        for qtype in DBAPI.query_types:
            key = DBAPI.__KEY_BASE + str(int(qtype))
            self.__redis.delete(key)

        if final:
            log.info("Waiting for DB sync worker to finish")
            sproc.join()

    def get_urls(self):
        with mdb.connect(self.conf.getDbname()) as con:
            q = 'SELECT uri FROM transactions'
            c = con.cursor()
            c.execute(q)
            return [x[0] for x in c.fetchall()]

    def get_known_defect_types(self, con):
        q = 'SELECT type, description FROM defectType'
        c = con.cursor()
        c.execute(q)
        return c.fetchall()

    def create_report_payload(self, cores=4, loglink=False):
        log = logging.getLogger(__name__)
        log.info("Creating report")
        if not cores:
            log.error("Cores: none")
        qt = Queue()
        tproc = Process(name="Transaction report",
                        target=DBAPI.__create_transactions,
                        args=(self.conf.getDbname(), qt, cores, loglink))

        ql = Queue()
        lproc = Process(name="Link report",
                        target=DBAPI.__create_links,
                        args=(self.conf.getDbname(), ql))

        qd = Queue()
        dproc = Process(name="Defect report",
                        target=DBAPI.__create_defects,
                        args=(self.conf.getDbname(), qd))

        log.debug("Starting report worker processes")
        tproc.start()
        lproc.start()
        dproc.start()

        log.debug("Getting data from workers")
        payload = dict()
        payload['defect'] = qd.get()
        log.info("Got defects")
        payload['link'] = ql.get()
        log.info("Got links")
        payload['transactions'] = qt.get()
        log.info("Got transactions")

        log.info("Joining")
        lproc.join()
        dproc.join()
        tproc.join()

        return payload

    def __fetchall(self, q):
        with mdb.connect(self.conf.getDbname()) as con:
            c = con.cursor()
            c.execute(q)
            return c.fetchall()

    def get_invalid_links(self):
        q = ('select transactions.uri, defect.evidence, defectType.type '
             'from defect '
             'inner join defectType on defect.type = defectType.id '
             'join transactions on transactions.id = defect.responseId '
             'where defectType.type = "badlink" or '
             'defectType.type = "timeout" '
             'order by defect.severity, transactions.uri')

        return self.__fetchall(q)

    def get_other_defects(self):
        query = ('select transactions.uri, defect.evidence, '
                 'defectType.description, defect.severity '
                 'from defect inner join defectType on '
                 'defect.type=defectType.id inner join transactions on '
                 'transactions.id=defect.responseId where '
                 'defectType.type != "badlink" and '
                 'defectType.type != "timeout" order by defect.severity desc,'
                 'defectType.type, transactions.uri')

        return self.__fetchall(query)

    def get_cookies(self):
        query = ('select transactions.uri, cookies.name, cookies.value '
                 'from cookies inner join transactions '
                 'on cookies.responseId = transactions.id')
        return self.__fetchall(query)

    @staticmethod
    def __create_transactions(dbname, queue, allowance, loglink):
        log = logging.getLogger(__name__)
        if allowance < 1:
            log.error("Wrong amount of processes: " + str(allowance))
            return

        with mdb.connect(dbname) as con:
            transactions = []
            q = ('SELECT id, method, responseStatus, contentType, '
                 'verificationStatus, depth, uri FROM transactions')

            c = con.cursor()
            c.execute(q)
            for row in c.fetchall():  # type(row): tuple
                transaction = dict()
                transaction['id'] = row[0]
                transaction['method'] = row[1]
                transaction['responseStatus'] = row[2]
                transaction['contentType'] = row[3]
                transaction['verificationStatus'] = row[4]
                transaction['depth'] = row[5]
                transaction['uri'] = row[6]
                if row[5] == 0:
                    transaction['parentId'] = transaction['id']
                transactions.append(transaction)

            log.info("%s transactions, processing in pool of %s processes" %
                     (str(len(transactions)), str(allowance)))

            with Pool(allowance) as pool:
                partial_process = partial(process_transaction, dbname=dbname, loglink=loglink)
                queue.put(pool.map(partial_process, transactions))

    @staticmethod
    def __create_links(dbname, queue):
        with mdb.connect(dbname) as con:
            c = con.cursor()
            links = []
            proc0 = 0
            total0 = 0
            good0 = 0
            q = ('SELECT link.findingId, responseTr.uri, link.toUri, '
                 'requestTr.verificationStatus, link.processed, requestId, '
                 'responseId FROM link '
                 'INNER JOIN transactions as requestTr '
                 'ON requestTr.id = link.requestId '
                 'INNER JOIN transactions as responseTr '
                 'ON responseTr.id = link.responseId')

            c.execute(q)

            for row in c.fetchall():
                link = dict()
                link['findingId'] = row[0]
                link['fromUri'] = row[1]
                link['good'] = (row[3] != 'VerificationStatus.done_ko')
                link['toUri'] = row[2]
                link['processed'] = (row[4] == 'true')
                link['requestId'] = row[5]
                link['responseId'] = row[6]
                links.append(link)
                if row[4]:
                    proc0 = proc0 + 1
                total0 = total0 + 1
                if link['good']:
                    good0 = good0 + 1

            if total0 == 0.0:
                perc0 = 0.0
            else:
                perc0 = proc0 / total0 * 100.0
            queue.put(links)

    @staticmethod
    def __create_defects(dbname, queue):
        with mdb.connect(dbname) as con:
            defects = []
            q = ('SELECT defect.findingId, defectType.type, '
                 'defectType.description, defect.evidence, defect.severity, '
                 'defect.responseId, transactions.uri FROM defect '
                 'INNER JOIN defectType ON defect.type = defectType.id '
                 'INNER JOIN transactions ON defect.responseId = '
                 'transactions.id')
            c = con.cursor()
            c.execute(q)
            for row in c.fetchall():
                defect = dict()
                defect['findingId'] = row[0]
                defect['type'] = row[1]
                defect['description'] = row[2]
                defect['evidence'] = row[3]
                defect['severity'] = row[4]
                defect['responseId'] = row[5]
                defect['uri'] = row[6]
                defects.append(defect)
            queue.put(defects)


def process_transaction(t, dbname, loglink):
    with mdb.connect(dbname) as con:
        c = con.cursor()
        if t['depth'] > 0 and loglink:
            q = ('SELECT link.responseId FROM link '
                 'WHERE link.requestId = ? '
                 'AND link.processed = "true" LIMIT 1')
            c.execute(q, [t['id']])
            try:
                t['parentId'] = c.fetchone()[0]
            except TypeError:
                t['parentId'] = -1
                logging.getLogger(__name__).error("No parent for link with " +
                                                  "requestId: %s (depth: %s)" %
                                                  (str(t['id']),
                                                   str(t['depth'])))

        q = ('SELECT uri FROM aliases WHERE transactionId = ?')
        c.execute(q, [t['id']])
        t['aliases'] = [row[0] for row in c.fetchall()]
        return t
