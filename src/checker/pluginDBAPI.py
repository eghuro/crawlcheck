"""Database connector.
For a plugin to access the database an API is provided.
Plugins receive a DBAPI instance with an interface for common actions
Parameters of connection to the database are set in DBAPIConfiguration
"""

import sqlite3 as mdb
from enum import Enum
import logging
import gc
from multiprocessing import Process, Queue, Pool
from functools import partial


class DBAPIconfiguration(object):
    """ Configuration class for DBAPI.

    Configuration is set through respective setters and read through getters.

    Attributes:
        dbname (str): Sqlite3 database file to use
    """

    def __init__(self):
        """Default constructor.
        """

        self.dbname = ""
        self.limit = 0

    def getDbname(self):
        """ Database name getter.
        """

        return self.dbname

    def setDbname(self, dbname):
        """Database name setter.

        Args:
            dbname: database name where data are stored
        """

        self.dbname = dbname

    def getLimit(self):
        return self.limit

    def setLimit(self, limit):
        self.limit = limit

class VerificationStatus(Enum):

    requested = "REQUESTED"
    done_ok = "DONE - OK"
    done_ko = "DONE - KO"
    done_ignored = "DONE - IGNORED"

class Query(Enum):

    transactions = 1
    link = 2
    defect = 5
    defect_types = 3
    aliases = 4
    cookies = 6
    transactions_load = 7
    transactions_status = 8
    link_status = 0

class TableError(LookupError):

    pass


class DBAPI(object):
    """ API for access to underlying database.
        Connection to the database is initiated in constructor and closed in
        destructor.
    """
    def __init__(self, conf):
        self.conf = conf
        self.limit = conf.getLimit()
        self.findingId = -1
        self.query_types = [Query.defect_types, Query.transactions, Query.transactions_load, Query.transactions_status, Query.aliases,  Query.link, Query.link_status, Query.defect, Query.cookies]
        self.queries = dict()
        self.queries[Query.link] = 'INSERT INTO link (findingId, toUri, requestId, responseId) VALUES (?,?,?,?)'
        self.queries[Query.defect_types] = 'INSERT INTO defectType (id, type, description) VALUES (?, ?, ?)'
        self.queries[Query.defect] = 'INSERT INTO defect (findingId, type, evidence, severity, responseId) VALUES (?, ?, ?, ?, ?)'
        self.queries[Query.cookies] = 'INSERT INTO cookies (findingId, name, value, responseId) VALUES (?, ?, ?, ?)'
        self.queries[Query.aliases] = 'INSERT INTO aliases (transactionId, uri) VALUES (?, ?)'
        self.queries[Query.transactions] = 'INSERT INTO transactions (id, method, uri, verificationStatus, depth) VALUES (?, ?, ?, ?, ?)'
        self.queries[Query.transactions_load] = 'UPDATE transactions SET verificationStatus = ?, uri = ?, contentType = ?, responseStatus = ? WHERE id = ?'
        self.queries[Query.transactions_status] = 'UPDATE transactions SET verificationStatus = ? WHERE id = ?'
        self.queries[Query.link_status] = 'UPDATE link SET processed = ? WHERE toUri = ?'
        self.logs = dict()
        for qtype in self.query_types:
            self.logs[qtype] = []
        self.defect_types = []
        self.defectId = -1
        self.defectTypesWithId = dict()
        self.bufferedQueries = 0

    def log(self, query, query_params):
        if query in self.logs:
            self.logs[query].append(query_params)
            self.bufferedQueries = self.bufferedQueries + 1
            if self.bufferedQueries > self.limit:
                self.sync()
                gc.collect()
        else:
            raise TableError()

    def log_link(self, parent_id, uri, new_id):
       self.findingId = self.findingId + 1
       self.log(Query.link, (str(self.findingId), uri, str(new_id), str(parent_id)))

    def log_defect(self, transactionId, name, additional, evidence, severity = 0.5):
        self.findingId = self.findingId + 1
        if name not in self.defect_types:
            self.defectId = self.defectId + 1
            self.log(Query.defect_types, (str(self.defectId), str(name), str(additional)))
            self.defect_types.append(name)
            self.defectTypesWithId[name] = self.defectId
        defId = self.defectTypesWithId[name]
        self.log(Query.defect, (str(self.findingId), str(defId), str(evidence), str(severity), str(transactionId)))

    def log_cookie(self, transactionId, name, value):
        self.findingId = self.findingId + 1
        self.log(Query.cookies, (str(self.findingId), str(name), str(value), str(transactionId)))
        
    def sync(self):
        logging.getLogger().info("Writing into database")
        with mdb.connect(self.conf.getDbname()) as con:
            try:
                cursor = con.cursor()

                for qtype in self.query_types:
                    cursor.executemany(self.queries[qtype], self.logs[qtype])

            except mdb.Error as e:
                self.error(e, con)

            else:
                for qtype in self.query_types:
                    self.logs[qtype] = []
                self.bufferedQueries = 0


    def error(self, e, con):
        con.rollback()
        log = logging.getLogger()
        log.error("SQL Error: "+str(e))

    def load_defect_types(self, con):
        query = 'SELECT type, id FROM defectType'
        cursor = con.cursor()
        cursor.execute(query)
        types = cursor.fetchall()
        for dt in types:
            if dt is not None:
                if dt[0] is not None:
                    self.defect_types.append(dt[0])
                    if dt[1] is not None:
                        self.defectTypesWithId[dt[0]] = dt[1]
        query = 'SELECT MAX(id) from defectType'
        cursor.execute(query)
        row = cursor.fetchone()
        if row is not None:
            if row[0] is not None:
                self.defectId = row[0]

    def load_finding_id(self, con):
        maxs = []
        for t in ['link', 'defect', 'cookies']:
            maxs.append(self.__load_max_finding_id(t, con))
        self.findingId =  max(maxs)

    def __load_max_finding_id(self, table, con):
        query = 'SELECT MAX(findingId) FROM %s' % (table)
        cursor = con.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        if row is not None:
            if row[0] is not None:
                return int(row[0])
        return 0

    def get_requested_transactions(self, con):
        q = 'CREATE TEMPORARY VIEW linkedUris AS SELECT link.toUri, transactions.id FROM link INNER JOIN transactions ON link.responseId = transactions.id'
        query = ('SELECT linkedUris.toUri AS uri, transactions.depth AS depth, linkedUris.id AS srcId, transactions.id AS idno'
                 ' FROM transactions LEFT JOIN linkedUris ON transactions.uri = linkedUris.toUri WHERE transactions.verificationStatus = ?')

        cursor = con.cursor()
        cursor.execute(q)
        cursor.execute(query, [str(VerificationStatus.requested)])
        data = cursor.fetchall()
        cursor.execute('DROP VIEW linkedUris')
        return data

    def get_seen_uris(self, con):
        query = 'SELECT uri FROM aliases'
        c = con.cursor()
        c.execute(query)
        return c.fetchall()

    def get_max_transaction_id(self, con):
        q = 'SELECT MAX(id) FROM transactions'
        cursor = con.cursor()
        cursor.execute(q)
        row = cursor.fetchone()
        if row is not None:
            if row[0] is not None:
                return row[0]
        return 0

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


    def create_report_payload(self):
        log = logging.getLogger(__name__)
        log.info("Creating report")
        qt = Queue()
        tproc = Process(target=DBAPI.__create_transactions, args=(self.conf.getDbname(), qt, 4))

        ql = Queue()
        lproc = Process(target=DBAPI.__create_links, args=(self.conf.getDbname(), ql))

        qd = Queue()
        dproc = Process(target=DBAPI.__create_defects, args=(self.conf.getDbname(), qd))

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

    @staticmethod
    def __create_transactions(dbname, queue, allowance):
        log = logging.getLogger(__name__)
        with mdb.connect(dbname) as con:
            transactions = []
            q = ('SELECT id, method, responseStatus, contentType, '
                 'verificationStatus, depth, uri FROM transactions')

            c = con.cursor()
            c.execute(q)
            for row in c.fetchall(): #type(row): tuple
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

            log.info("%s transactions, processing in pool of %s processes" % (str(len(transactions)), str(allowance)))

            with Pool(allowance) as pool:
                partial_process = partial(process_transaction, dbname=dbname)
                queue.put(pool.map(partial_process, transactions))

    @staticmethod
    def __create_links(dbname, queue):
        with mdb.connect(dbname) as con:
            c = con.cursor()
            links = []
            proc0 = 0
            total0 = 0
            good0 = 0
            q = ('SELECT link.findingId, transactions.uri, '
                 'transactions.verificationStatus, link.toUri, link.processed, '
                 'link.requestId, link.responseId '
                 'FROM link '
                 'INNER JOIN transactions ON link.requestId = transactions.id ')
            c.execute(q)
            for row in c.fetchall():
                link = dict()
                link['findingId'] = row[0]
                link['fromUri'] = row[1]
                link['good'] = (row[2] != 'VerificationStatus.done_ko')
                link['toUri'] = row[3]
                link['processed'] = row[4]
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
                 'INNER JOIN transactions ON defect.responseId = transactions.id')
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


def process_transaction(t, dbname):
    with mdb.connect(dbname) as con:
        c = con.cursor()
        if t['depth'] > 0:
            q = ('SELECT link.responseId FROM link '
                 'WHERE link.requestId = ? '
                 'AND link.processed = "true" LIMIT 1')
            c.execute(q, [t['id']])
            try:
                t['parentId'] = c.fetchone()[0]
            except TypeError:
                t['parentId'] = -1
                logging.getLogger().error("No parent for link with requestId: %s (depth: %s)" % (str(t['id']), str(t['depth'])))

        q = ('SELECT uri FROM aliases WHERE transactionId = ?')
        c.execute(q, [t['id']])
        t['aliases'] = [row[0] for row in c.fetchall()]
        return t
