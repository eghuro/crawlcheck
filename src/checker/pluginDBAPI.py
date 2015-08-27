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


class TransactionInfo(object):
    """Container with necessary information about a transaction.
    """

    def __init__(self, tid, content, contentType, uri):
        self.tid = tid
        self.content = content
        self.ctype = contentType
        self.uri = uri

    def getId(self):
        return self.tid

    def getContent(self):
        return self.content

    def getContentType(self):
        return self.ctype

    def getUri(self):
        return self.uri

    def setUri(self, uri):
        self.uri = uri


class DBAPI(object):
    """ API for access to underlying database.
        Connection to the database is initiated in constructor and closed in
        destructor.
    """
    def __init__(self, conf):
        self.con = mdb.connect(conf.getUri(), conf.getUser(),
                               conf.getPassword(), conf.getDbname())
        self.cursor = self.con.cursor()

    def __del__(self):
        if self.con:
            self.con.close()

    def getTransaction(self):
        """ Get next transaiction from the database and mark it as in process.
            If there is a MySQL error, then rollback.
            For content-type, everything after the first ; character is omitted
            making content-type like application/jVscript, text/css, text/html
            instead of text/html; charset=utf-8

            Return: transaction info object, transaction ID -1 means something
                    went wrong.
        """
        transactionId = -1
        content = ""
        contentType = ""
        uri = ""

        try:
            statusId = DBAPI.getUnverifiedStatusId()
            idSelectorQuery = ('SELECT @A:=MAX(id)  FROM transaction WHERE '
                               'method = \'GET\' AND responseStatus  = 200 AND'
                               ' verificationStatusId = ' + str(statusId) + '')
            contentSelectorQuery = ('SELECT id, content, contentType, uri FROM'
                                    ' transaction WHERE id = @A')
            self.cursor.execute(idSelectorQuery)
            self.cursor.execute(contentSelectorQuery)
            row = self.cursor.fetchone()
            if row is not None:
                assert len(row) == 4
                if row[0] is not None:
                    assert row[1] is not None
                    assert row[2] is not None
                    assert row[3] is not None
                    transactionId = row[0]
                    content = row[1]
                    contentType = row[2].split(';')[0]
                    # text/html; charset=utf-8 -> text/html
                    uri = row[3]

                    statusId = DBAPI.getProcessingStatusId()
                    statusUpdateQuery = ('UPDATE transaction '
                                         'SET verificationStatusId = '
                                         ''+(statusId)+' '
                                         'WHERE id = @A')
                    self.cursor.execute(statusUpdateQuery)
            self.con.commit()

        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return TransactionInfo(transactionId, content, contentType, uri)

    def setDefect(self, transactionId, defectType, line, evidence):
        """ Insert new defect discovered by a plugin into database.
            If defectType doesn't exist, add it to database.
            If there is a MySQL error, then rollback.

            Return: True, if a new defect is set into defect and finding tables
                    False, if something went wrong
        """
        try:
            query = ('INSERT INTO finding (responseId) VALUES ('
                     '' + str(transactionId) + ')')
            self.cursor.execute(query)
            findingId = self.cursor.lastrowid

            self.cursor.execute('SELECT id FROM defectType WHERE type = "'
                                '' + str(defectType)+'" LIMIT 1')
            row = self.cursor.fetchone()
            if row is not None:
                if row[0] is not None:
                    defectTypeId = row[0]
                else:
                    defectTypeId = self.putNewDefectType(defectType)
            else:
                defectTypeId = self.putNewDefectType(defectType)

            query = ('INSERT INTO defect (findingId, type, location, evidence) '
                     'VALUES (' + str(findingId) + ', ' + str(defectTypeId) + ', '
                     '' + str(line) + ', "'
                     '' + self.con.escape_string(evidence.encode('utf-8')) + ''
                     '" )')
            self.cursor.execute(query)
            self.con.commit()
            return True

        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return False

    def putNewDefectType(self, defectType):
        self.cursor.execute('INSERT INTO defectType (type) VALUES ("'
                            ''+defectType+'")')
        return self.cursor.lastrowid

    def setLink(self, transactionId, toUri):
        try:
            query = ('INSERT INTO transaction (method, uri, origin, '
                     'verificationStatusId, rawRequest) VALUES (\'GET\', "'
                     '' + self.con.escape_string(toUri) + '", \'CHECKER\', '
                     ''+str(DBAPI.getRequestedStatusId())+', "'
                     '' + self.con.escape_string(self.getRequest(toUri)) + '")')
            self.cursor.execute(query)
            reqId = self.cursor.lastrowid

            query = ('INSERT INTO finding (responseId) VALUES ('
                     '' + str(transactionId) + ')')
            self.cursor.execute(query)
            findingId = self.cursor.lastrowid

            query = ('INSERT INTO link (findingId, toUri, requestId) VALUES ('
                     '' + str(findingId) + ', '
                     '"' + self.con.escape_string(toUri) + '", '+str(reqId)+')')
            self.cursor.execute(query)
            self.con.commit()
            return reqId

        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d: %s" % (e.args[0], e.args[1])

        return None

    def getFinishedStatusId():
        return 5

    def getProcessingStatusId():
        return 4

    def getUnverifiedStatusId():
        return 3

    def getRequestedStatusId():
        return 1

    def setFinished(self, transactionId):
        """ Mark in the database that we are done with verification of a
            particular transaction.

            Return: True, if change was made, false if MySQL error occured
        """
        try:
            statusId = DBAPI.getFinishedStatusId()
            query = ('UPDATE transaction SET verificationStatusId = '
                     '' + str(statusId) + ''
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

    def setResponse(self, reqId, status, contentType, content, raw):
        """ Set response into database.

            Return true, if transaction was updated, false otherwise.
        """
        try:
            query = ('UPDATE transaction SET responseStatus = '
                     '' + str(status) + ', contentType = "' + contentType + '", '
                     'verificationStatusUd = '
                     '' + str(DBAPI.getUnverifiedStatusId()) + ', content = "'
                     '' + content + ''
                     '", raw = "' + raw + '" WHERE id = ' + str(reqId) + '')
            self.cursor.execute(query)
            self.con.commit()
            return True
        except mdb.Error, e:
            if self.con:
                self.con.rollback()
            print "Error %d %s" % (e.args[0], e.args[1])
            return False
