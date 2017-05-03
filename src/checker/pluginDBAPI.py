"""Database connector.
For a plugin to access the database an API is provided.
Plugins receive a DBAPI instance with an interface for common actions
Parameters of connection to the database are set in DBAPIConfiguration
"""

import sqlite3 as mdb
from enum import Enum
import logging


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
        self.tables = [Table.defect_types, Table.transactions, Table.link_defect]
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
        query = 'SELECT MAX(findingId) FROM ' + table
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
        query = 'SELECT uri FROM transactions'
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
                    logging.getLogger().error("No parent for link with requestId: " + t['id'] + " (depth: " + t['depth'] + ")")

        payload['link'] = []
        q = ('SELECT link.findingId, transactions.uri, link.toUri, '
             'link.processed, link.requestId, link.responseId FROM '
             'link INNER JOIN transactions ON link.responseId = transactions.id')
        c.execute(q)
        for row in c.fetchall():
            link = dict()
            link['findingId'] = row[0]
            link['fromUri'] = row[1]
            link['toUri'] = row[2]
            link['processed'] = row[3]
            link['requestId'] = row[4]
            link['responseId'] = row[5]
            payload['link'].append(link)

        payload['defect'] = []
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

        return payload
