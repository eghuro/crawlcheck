"""Database connector.
For a plugin to access the database an API is provided.
Plugins receive a DBAPI instance with an interface for common actions
Parameters of connection to the database are set in DBAPIConfiguration
"""

import MySQLdb as mdb

class DBAPIconfiguration(object):
    """ Configuration class for DBAPI.

    Configuration is set through respective setters and read through getters.

    Attributes:
        uri (str): Database server uri, including a port
        user (str): User name to connect to the DB as
        password (str): Password for the user
        dbname (str): Database to use
    """

    def __init__(self):
        """Default constructor.
        """

        self.uri = ""
        self.user = ""
        self.password = ""
        self.dbname = ""

    def getUri(self):
        """Database server's URI getter.
        """

        return self.uri

    def getUser(self):
        """ Username getter.
        """

        return self.user

    def getPassword(self):
        """ Password getter.
        """

        return self.password

    def getDbname(self):
        """ Database name getter.
        """

        return self.dbname

    def setUri(self, uri):
        """Database server's URI setter.

        Args:
            uri: full uri of the database server
        """

        self.uri = uri

    def setUser(self, user):
        """Username setter.

        Args:
            user: username for connection to the database
        """

        self.user = user

    def setPassword(self, pwd):
        """Password setter.

        Args:
            pwd: password for the user used for connection to the database
        """

        self.password = pwd

    def setDbname(self, dbname):
        """Database name setter.

        Args:
            dbname: database name where data are stored
        """

        self.dbname = dbname

class TransactionInfo:
    def __init__(self, tid, content):
        self.tid = tid
        self.content = content

    def getId(self):
        return self.tid

    def getContent(self):
        return self.content

    def getContentType(self):
        return "text/html"

class DBAPI:
    def __init__(self, conf):
        self.con = mdb.connect(conf.getUri(), conf.getUser(), conf.getPassword(), conf.getDbname())
        self.cursor = self.con.cursor()

    def __del__(self):
        if self.con:
            self.con.close()

    def getTransaction(self):
        transactionId = -1
        content = ""

        try:
            query = ('SELECT @A:=MAX(transaction.id), content '
                     'FROM transaction '
                     'INNER JOIN verificationStatus '
                     'ON verificationStatus.id = transaction.id '
                     'WHERE transaction.responseStatus = 200 '
                     'AND transaction.contentType = "text/html" '
                     'AND transaction.method = \'GET\' '
                     'AND verificationStatus.status = "UNVERIFIED"')
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            if row is not None:
                if row[0] is not None:
                    transactionId = row[0]
                    print transactionId
                    assert row[1] is not None
                    content = row[1]
                    query = ('UPDATE transaction '
                             'SET verificationStatusId = '
                             '(SELECT id FROM verificationStatus WHERE status = "PROCESSING") '
                             'WHERE id = @A')
                    self.cursor.execute(query)
                    self.con.commit()

        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return TransactionInfo(transactionId, content)

    def setDefect(self, transactionId, defectType, line, evidence):
        try:
            query = ('INSERT INTO finding (responseId) VALUES (' + str(transactionId) + ')')
            self.cursor.execute(query)
            findingId = self.cursor.lastrowid
            #self.cursor.execute("SELECT id FROM defectType WHERE type = " + str(defectType))
            #row = self.cursor.fetchone()
            #if row is not None:
                #if row[0] is not None:
                    #defectTypeId = self.cursor.fetchone()[0]
            defectTypeId = defectType
            query = ('INSERT INTO defect (findingId, type, location, evidence) '
                     'VALUES (' + str(findingId) + ', ' + str(defectTypeId) + ', '
                     '' + str(line) + ', "' + self.con.escape_string(evidence) + '" )')
            self.cursor.execute(query)
            self.con.commit()
            return True
                #else:
                    #self.con.rollback()
                    #return False
            #else:
                #self.con.rollback()
                #return False

        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return False

    def setLink(self, transactionId, toUri):
        try:
            query = ('INSERT INTO finding (responseId) VALUES (' + str(transactionId) + ')')
            self.cursor.execute(query)
            findingId = self.cursor.lastrowid
            query = ('INSERT INTO link (findingId, toUri) VALUES (' + str(findingId) + ', '
                     '' + self.con.escape_string(toUri) + ')')
            self.cursor.execute(query)
            return True

        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return False

    def setFinished(self, transactionId, status):
        try:
            query = ('UPDATE transaction SET verificationStatusId = ' + str(statusId) + ''
                     ' WHERE id = ' + str(transactionId) + '')
            self.cursor.execute(query)
            self.con.commit()
            return True

        except mdb.Error, e:
            if self.con():
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return False
