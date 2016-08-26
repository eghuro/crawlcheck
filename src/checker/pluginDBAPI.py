"""Database connector.
For a plugin to access the database an API is provided.
Plugins receive a DBAPI instance with an interface for common actions
Parameters of connection to the database are set in DBAPIConfiguration
"""

import sqlite3 as mdb
from enum import Enum


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

    def log(self, table, query_pair):
        if table in self.logs:
            self.logs[table].append(query_pair)
        else:
            raise TableError()

    def log_link(self, parent_id, uri, new_id):
       self.findingId = self.findingId + 1
       self.log(Table.finding, ('INSERT INTO finding (id, responseId) VALUES (?, ?)', [str(self.findingId), str(parent_id)]) )
       self.log(Table.link_defect, ('INSERT INTO link (findingId, toUri, requestId) VALUES (?, ?, ?)', [str(self.findingId), str(uri), str(new_id)]) )

    def log_defect(self, transactionId, name, additional):
        self.findingId = self.findingId + 1
        self.log(Table.finding, ('INSERT INTO finding (id, responseId) VALUES (?, ?)', [str(self.findingId), str(transactionId)]))
        if name not in self.defect_types:
            self.log(Table.defect_types, ('INSERT INTO defectType (type) VALUES (?)', [str(name)]))
            self.defect_types.append(name)
        self.log(Table.link_defect, ('INSERT INTO defect (findingId, type, evidence) VALUES (?, ?, ?)', [str(self.findingId), str(name), str(additional)]))
        
    def sync(self):
        try:
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
        for record in self.logs[table]:
            print("Executing "+record[0]+" with "+str(record[1]))
            cursor.execute(record[0], record[1])

    def error(self, e):
        self.con.rollback()
        print("Error?!?"+str(e))

    def load_defect_types(self):
        query = 'SELECT type FROM defectType'
        cursor = self.con.get_cursor()
        cursor.execute(query)
        types = cursor.fetchall()
        for dt in types:
            if dt is not None:
                if dt[0] is not None:
                    self.defect_types.append(dt[0])

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
        return -1
        return data
