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
            statusId = self.getUnverifiedStatusId()
            idSelectorQuery = ('SELECT @A:=MAX(id)  FROM transaction WHERE method = \'GET\' AND responseStatus  = 200 AND contentType LIKE "text/html%" AND verificationStatusId = '+str(statusId) +'')
            contentSelectorQuery = ('SELECT id, content FROM transaction WHERE id = @A')
            self.cursor.execute(idSelectorQuery)           
            self.cursor.execute(contentSelectorQuery)
            row = self.cursor.fetchone()
            if row is not None:
               if row[0] is not None:
                   assert row[1] is not None
                   transactionId = row[0]
                   content = row[1]

                   statusId = self.getProcessingStatusId()
                   statusUpdateQuery = ('UPDATE transaction '
                                        'SET verificationStatusId = '+str(statusId)+' '
                                        'WHERE id = @A')
                   self.cursor.execute(statusUpdateQuery)
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

            self.cursor.execute("SELECT id FROM defectType WHERE type = \"" + str(defectType)+"\" LIMIT 1")
            row = self.cursor.fetchone()
            if row is not None:
                if row[0] is not None:
                    defectTypeId = self.cursor.fetchone()[0]
                else:
                    defectTypeId = putNewDefectType(defectType);
            else:
                defectTypeId = putNewDefectType(defectType);

            query = ('INSERT INTO defect (findingId, type, location, evidence) '
                     'VALUES (' + str(findingId) + ', ' + str(defectTypeId) + ', '
                     '' + str(line) + ', "' + self.con.escape_string(evidence) + '" )')
            self.cursor.execute(query)
            self.con.commit()
            return True


        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return False

    def putNewDefectType(self, defectType):
        self.cursor.execute("INSERT INTO defectType (type) VALUES (\""+defectType+"\")")
        return self.cursor.lastrowId

    def setLink(self, transactionId, toUri):
        try:
            query = ('INSERT INTO transaction (method, uri, origin, verificationStatusId, rawRequest) VALUES (\'GET\', "'
                     '' + self.con.escape_string(toUri) + '", \'CHECKER\', '+self.getRequestedStatusId()+', "'
                     '' + self.con.escape_string(self.getRequest(toUri))+'")')
            self.cursor.execute(query)
            transactionId = self.cursor.lastrowid

            query = ('INSERT INTO finding (responseId) VALUES (' + str(transactionId) + ')')
            self.cursor.execute(query)
            findingId = self.cursor.lastrowid

            query = ('INSERT INTO link (findingId, toUri, requestId) VALUES (' + str(findingId) + ', '
                     '"' + self.con.escape_string(toUri) + '", '+transactionId+')')
            self.cursor.execute(query)
            self.con.commit()
            return True

        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return False

    def getFinishedStatusId(self):
        return 5

    def getProcessingStatusId(self):
        return 4

    def getUnverifiedStatusId(self):
        return 3

    def getRequestedStatusId(self):
        return 1

    def setFinished(self, transactionId):
        try:
            statusId = self.getFinishedStatusId()
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

    def getRequest(self, toUri):
        return "GET "+toUri+" HTTP/1.1\r\n\r\n"
