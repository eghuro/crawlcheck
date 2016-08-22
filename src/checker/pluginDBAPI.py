"""Database connector.
For a plugin to access the database an API is provided.
Plugins receive a DBAPI instance with an interface for common actions
Parameters of connection to the database are set in DBAPIConfiguration
"""

import sqlite3 as mdb
from enum import Enum


class VerificationStatus(Enum):

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
        self.findingId = 0
        self.logs = dict()
        self.logs[Table.transactions] = []
        self.logs[Table.finding] = []
        self.logs[Table.link_defect] = []
        self.logs[Table.defect_types] = []
        self.defect_types = []

    def log(self, table, query_pair):
        if table in self.logs:
            self.logs[table].append(query_pair)
        else:
            raise

    def log_link(self, parent_id, uri, new_id):
       self.log(Table.finding, ('INSERT INTO finding (id, responseId) VALUES (?, ?)', [str(self.findingId), str(parent_id)]) )
       self.log(Table.link_defect, ('INSERT INTO link (findingId, toUri, requestId) VALUES (?, ?, ?)', [str(self.findingId), str(uri), str(new_id)] )
       self.findingId = self.findingId + 1

    def log_defect(self, transactionId, name, additional):
        self.log(Table.finding, ('INSERT INTO finding (id, responseId) VALUES (?, ?)', [str(self.findingId), str(transactionId)])
        if name not in self.defect_types:
            self.log(Table.defect_types, ('INSERT INTO defectType (type) VALUES (?)', [str(name)]))
            self.defect_types.append(name)
        self.log(Table.link_defect, ('INSERT INTO defect (findingId, type, evidence) VALUES (?, ?, ?)', [str(self.findingId), str(name), str(additional)])
        self.findingId = self.findingId + 1

    def sync(self):
        try:
            cursor = self.con.get_cursor()

            #first defect types
            #then transactions
            #only then findings depending on transactions
            #and links and defects depending on findings and possibly defect types at the end

            for table in [Table.defect_types, Table.transactions, Table.finding, Table.link_defect]:
                self.__sync_table(cursor, table]

            self.con.commit()

         except mdb.Error as e:
            self.error(e)

    def __sync_table(self, cursor, table):
        for record in self.logs[table]:
            cursor.execute(record[0], record[1])

    def error(self, e):
        self.con.rollback()
        print("Error?!? %s", (e.args[0]))
