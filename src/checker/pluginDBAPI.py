"""Database connector.
For a plugin to access the database an API is provided.
Plugins receive a DBAPI instance with an interface for common actions
Parameters of connection to the database are set in DBAPIConfiguration
"""

import sqlite3 as mdb
from enum import Enum
import logging
import gc


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

class Table(Enum):

    transactions = 1
    link_defect = 2
    defect_types = 3
    aliases = 4

class TableError(LookupError):

    pass

class Connector(object):
    def __init__(self, conf):
        self.con = mdb.connect(conf.getDbname())
        self.cursor = self.con.cursor()

    def get_cursor(self):
        return self.cursor

    def commit(self):
        self.con.commit()

    def rollback(self):
        if self.con:
            self.con.rollback()

    def __del__(self):
        if self.con:
            self.con.close()


class DBAPI(object):
    """ API for access to underlying database.
        Connection to the database is initiated in constructor and closed in
        destructor.
    """
    def __init__(self, conf):
        self.con = Connector(conf)
        self.limit = conf.getLimit()
        self.findingId = -1
        self.tables = [Table.defect_types, Table.transactions, Table.aliases,  Table.link_defect]
        self.logs = dict()
        for table in self.tables:
            self.logs[table] = []
        self.defect_types = []
        self.defectId = -1
        self.defectTypesWithId = dict()
        self.bufferedQueries = 0

    def log(self, table, query_pair):
        if table in self.logs:
            self.logs[table].append(query_pair)
            self.bufferedQueries = self.bufferedQueries + 1
            if self.bufferedQueries > self.limit:
                self.sync()
                gc.collect()
        else:
            raise TableError()

    def log_link(self, parent_id, uri, new_id):
       self.findingId = self.findingId + 1
       self.log(Table.link_defect, ('INSERT INTO link (findingId, toUri, requestId, responseId) VALUES (?, ?, ?, ?)', [str(self.findingId), uri, str(new_id), str(parent_id)]) )

    def log_defect(self, transactionId, name, additional, evidence, severity = 0.5):
        self.findingId = self.findingId + 1
        if name not in self.defect_types:
            self.defectId = self.defectId + 1
            self.log(Table.defect_types, ('INSERT INTO defectType (id, type, description) VALUES (?, ?, ?)', [str(self.defectId), str(name), str(additional)]))
            self.defect_types.append(name)
            self.defectTypesWithId[name] = self.defectId
        defId = self.defectTypesWithId[name]
        self.log(Table.link_defect, ('INSERT INTO defect (findingId, type, evidence, severity, responseId) VALUES (?, ?, ?, ?, ?)', [str(self.findingId), str(defId), str(evidence), str(severity), str(transactionId)]))

    def log_cookie(self, transactionId, name, value):
        self.findingId = self.findingId + 1
        self.log(Table.link_defect, ('INSERT INTO cookies (findingId, name, value, responseId) VALUES (?, ?, ?, ?)', [str(self.findingId), str(name), str(value), str(transactionId)]))
        
    def sync(self):
        try:
            logging.getLogger().info("Writing into database")
            cursor = self.con.get_cursor()

            #first defect types
            #then transactions
            #only then findings depending on transactions
            #and links and defects depending on findings and possibly defect types at the end

            for table in self.tables:
                self.__sync_table(cursor, table)

            self.con.commit()

        except mdb.Error as e:
            self.error(e)

        else:
            for table in self.tables:
                self.logs[table] = []
            self.bufferedQueries = 0

    def __sync_table(self, cursor, table):
        #log.info("Imagine I execute all the SQL commands now ...")
        for record in self.logs[table]:
            #log.debug("SQL: "+record[0]+" with "+str(record[1]))
            cursor.execute(record[0], record[1])

    def error(self, e):
        self.con.rollback()
        log = logging.getLogger()
        log.error("SQL Error: "+str(e))

    def load_defect_types(self):
        query = 'SELECT type, id FROM defectType'
        cursor = self.con.get_cursor()
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

    def load_finding_id(self):
        maxs = []
        for t in ['link', 'defect', 'cookies']:
            maxs.append(self.__load_max_finding_id(t))
        self.findingId =  max(maxs)

    def __load_max_finding_id(self, table):
        query = 'SELECT MAX(findingId) FROM %s' % (table)
        cursor = self.con.get_cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        if row is not None:
            if row[0] is not None:
                return int(row[0])
        return 0

    def get_requested_transactions(self):
        q = 'CREATE TEMPORARY VIEW linkedUris AS SELECT link.toUri, transactions.id FROM link INNER JOIN transactions ON link.responseId = transactions.id'
        query = ('SELECT linkedUris.toUri AS uri, transactions.depth AS depth, linkedUris.id AS srcId, transactions.id AS idno'
                 ' FROM transactions LEFT JOIN linkedUris ON transactions.uri = linkedUris.toUri WHERE transactions.verificationStatus = ?')

        cursor = self.con.get_cursor()
        cursor.execute(q)
        cursor.execute(query, [str(VerificationStatus.requested)])
        data = cursor.fetchall()
        cursor.execute('DROP VIEW linkedUris')
        return data

    def get_seen_uris(self):
        query = 'SELECT uri FROM aliases'
        c = self.con.get_cursor()
        c.execute(query)
        return c.fetchall()

    def get_max_transaction_id(self):
        q = 'SELECT MAX(id) FROM transactions'
        cursor = self.con.get_cursor()
        cursor.execute(q)
        row = cursor.fetchone()
        if row is not None:
            if row[0] is not None:
                return row[0]
        return 0

    def get_known_defect_types(self):
        q = 'SELECT type, description FROM defectType'
        c = self.con.get_cursor()
        c.execute(q)
        return c.fetchall()

    def create_report_payload(self):
        payload = dict()
        payload['visual-data'] = dict()

        #TODO: 3 parallel processes
        payload['transactions'] = []
        q = ('SELECT id, method, responseStatus, contentType, '
             'verificationStatus, depth, uri FROM transactions')

        c = self.con.get_cursor()
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
            payload['transactions'].append(transaction)

        for t in payload['transactions']:
            if t['depth'] > 0:
                q = ('SELECT link.responseId FROM link '
                     'WHERE link.requestId = ? '
                     'AND link.processed = "true"')
                c.execute(q, [t['id']])
                try:
                    t['parentId'] = c.fetchone()[0]
                except TypeError:
                    t['parentId'] = -1
                    logging.getLogger().error("No parent for link with requestId: %s (depth: %s)" % (str(t['id'), str(t['depth'])))
            q = ('SELECT uri FROM aliases WHERE transactionId = ?')
            c.execute(q, [t['id']])
            t['aliases'] = [row[0] for row in c.fetchall()]

        payload['link'] = []
        proci0 = 0
        total0 = 0
        good0 = 0
        q = ('SELECT link.findingId, transactions.uri, '
             'transactions.verificationStatus, link.toUri, link.processed, '
             'link.requestId '
             'FROM link '
             'INNER JOIN transactions ON link.requestId = transactions.id ')
             #'INNER JOIN defect ON defect.responseId = link.responseId '
             #'INNER JOIN defectType ON defect.type = defectType.id '
             #'WHERE defectType.type = "badlink"')
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
            payload['link'].append(link)
            if row[4]:
                proc0 = proc0 + 1
            total0 = total0 + 1
            if link['good']:
                good0 = good0 + 1

        if total0 == 0.0:
            perc0 = 0.0
        else:
            perc0 = proc0 / total0 * 100.0

        #payload['visual-data']['processed-pie'] = [[0, perc0, "black"], [perc0, 100, "gray"]]
        #if proc0 == 0.0:
        #    perc1 = 0.0
        #else:
        #    perc1 = good0 / proc0 * 100.0
        #payload['visual-data']['processed-pie'] = [[0, perc1, "good"], [perc1, 100, "red"]]

        payload['defect'] = []
        #payload['visual-data']['defect-type-count'] = dict()
        #payload['visual-data']['defect-type-severity'] = dict()

        q = ('SELECT defect.findingId, defectType.type, '
             'defectType.description, defect.evidence, defect.severity, '
             'defect.responseId, transactions.uri FROM defect '
             'INNER JOIN defectType ON defect.type = defectType.id '
             'INNER JOIN transactions ON defect.responseId = transactions.id')
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
            payload['defect'].append(defect)
            #if row[1] not in payload['visual-data']['defect-type-count']:
            #    payload['visual-data']['defect-type-count'][row[1]] = 0
            #payload['visual-data']['defect-type-count'][row[1]] = payload['visual-data']['defect-type-count'][row[1]] + 1
            #payload['visual-data']['defect-type-severity'][row[1]] = row[4]
        #payload['visual-data']['defect-type-count-array'] = [payload['visual-data']['defect-type-count'][key] for key in payload['visual-data']['defect-type-count'].keys()]
        #payload['visual-data']['defect-type-label-array'] = [key for key in payload['visual-data']['defect-type-count'].keys()]
        #payload['visual-data']['severity-values'] = list(set([payload['visual-data']['defect-type-severity'][t] for t in payload['visual-data']['defect-type-severity'].keys()]))

        return payload
