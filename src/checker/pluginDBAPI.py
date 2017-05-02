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

class VerificationStatus(Enum):

    requested = 1
    done_ok = 3
    done_ko = 4
    done_ignored = 5

class Table(Enum):

    transactions = 1
    finding = 2
    link_defect = 3
    defect_types = 4

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
        self.findingId = -1
        self.tables = [Table.defect_types, Table.transactions, Table.finding, Table.link_defect]
        self.logs = dict()
        for table in self.tables:
            self.logs[table] = []
        self.defect_types = []
        self.defectId = -1
        self.defectTypesWithId = dict()

    def log(self, table, query_pair):
        if table in self.logs:
            self.logs[table].append(query_pair)
        else:
            raise TableError()

    def log_link(self, parent_id, uri, new_id):
       self.findingId = self.findingId + 1
       self.log(Table.finding, ('INSERT INTO finding (id, responseId) VALUES (?, ?)', [str(self.findingId), str(parent_id)]) )
       self.log(Table.link_defect, ('INSERT INTO link (findingId, toUri, requestId) VALUES (?, ?, ?)', [str(self.findingId), uri, str(new_id)]) )

    def log_defect(self, transactionId, name, additional, evidence, severity = 0.5):
        self.findingId = self.findingId + 1
        self.log(Table.finding, ('INSERT INTO finding (id, responseId) VALUES (?, ?)', [str(self.findingId), str(transactionId)]))
        if name not in self.defect_types:
            self.defectId = self.defectId + 1
            self.log(Table.defect_types, ('INSERT INTO defectType (id, type, description) VALUES (?, ?, ?)', [str(self.defectId), str(name), str(additional)]))
            self.defect_types.append(name)
            self.defectTypesWithId[name] = self.defectId
        defId = self.defectTypesWithId[name]
        self.log(Table.link_defect, ('INSERT INTO defect (findingId, type, evidence, severity) VALUES (?, ?, ?, ?)', [str(self.findingId), str(defId), str(evidence), str(severity)]))

    def log_cookie(self, transactionId, name, value):
        self.findingId = self.findingId + 1
        self.log(Table.finding, ('INSERT INTO finding (id, responseId) VALUES (?,?)', [str(self.findingId), str(transactionId)]))
        self.log(Table.link_defect, ('INSERT INTO cookies (findingId, name, value) VALUES (?, ?, ?)', [str(self.findingId), str(name), str(value)]))
        
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
        query = 'SELECT MAX(id) FROM finding'
        cursor = self.con.get_cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        if row is not None:
            if row[0] is not None:
                self.findingId = row[0]

    def get_requested_transactions(self):
        q = 'CREATE TEMPORARY VIEW linkedUris AS SELECT link.toUri, transactions.id FROM link INNER JOIN finding ON link.findingId = finding.id INNER JOIN transactions ON finding.responseId = transactions.id'
        query = ('SELECT linkedUris.toUri AS uri, transactions.depth AS depth, linkedUris.id AS srcId, transactions.id AS idno'
                 ' FROM transactions LEFT JOIN linkedUris ON transactions.uri = linkedUris.toUri WHERE transactions.verificationStatusId = ?')

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

        payload['transactions'] = []
        q = ('SELECT id, method, responseStatus, contentType, '
             'verificationStatusId, depth, uri FROM transactions')
        c = self.con.get_cursor()
        c.execute(q)
        for row in c.fetchall(): #type(row): tuple
            transaction = dict()
            transaction['id'] = row[0]
            transaction['method'] = row[1]
            transaction['responseStatus'] = row[2]
            transaction['contentType'] = row[3]
            transaction['verificationStatusId'] = row[4]
            transaction['depth'] = row[5]
            transaction['uri'] = row[6]
            payload['transactions'].append(transaction)

        payload['link'] = []
        q = ('SELECT link.findingId, transactions.uri, link.toUri, '
             'link.processed, link.requestId, finding.responseId FROM '
             'link INNER JOIN finding ON link.findingId = finding.id '
             'INNER JOIN transactions ON finding.responseId = transactions.id')
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
             'finding.responseId, transactions.uri FROM defect '
             'INNER JOIN defectType ON defect.type = defectType.id '
             'INNER JOIN finding on defect.findingId = finding.id '
             'INNER JOIN transactions ON finding.responseId = transactions.id')
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
