"""Database connector.
For a plugin to access the database an API is provided.
Plugins receive a DBAPI instance with an interface for common actions
Parameters of connection to the database are set in DBAPIConfiguration
"""

import sqlite3 as mdb
import urllib


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
        self.con = mdb.connect(conf.getDbname())
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
            idSelectorQuery = ('SELECT MAX(id)  FROM transactions WHERE '
                               'method = \'GET\' AND responseStatus  = 200 AND'
                               ' verificationStatusId = ?') 
            contentSelectorQuery = ('SELECT id, content, contentType, uri FROM'
                                    ' transactions WHERE id = ?')
            self.cursor.execute(idSelectorQuery, [str(statusId)])
            row = self.cursor.fetchone()
            if row[0] is not None:
                maxid = row[0]
                self.cursor.execute(contentSelectorQuery, [str(maxid)])
                row = self.cursor.fetchone()
                if row is not None: 
                  if row[0] is not None:
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
                        statusUpdateQuery = ('UPDATE transactions '
                                         'SET verificationStatusId = ?'
                                         'WHERE id = ?')
                    self.cursor.execute(statusUpdateQuery, [str(statusId), str(maxid)])
                self.con.commit()
        except mdb.Error, e:
            self.error(e)

        return TransactionInfo(transactionId, content, contentType, urllib.unquote(uri).decode('utf-8'))

    def setDefect(self, transactionId, defectType, line, evidence):
        """ Insert new defect discovered by a plugin into database.
            If defectType doesn't exist, add it to database.
            If there is a MySQL error, then rollback.

            Return: True, if a new defect is set into defect and finding tables
                    False, if something went wrong
        """
        try:
            query = ('INSERT INTO finding (responseId) VALUES (?)')
            self.cursor.execute(query, [str(transactionId)])
            findingId = self.cursor.lastrowid

            self.cursor.execute('SELECT id FROM defectType WHERE type = ? LIMIT 1', [str(defectType)])
            row = self.cursor.fetchone()
            if row is not None:
                if row[0] is not None:
                    defectTypeId = row[0]
                else:
                    defectTypeId = self.putNewDefectTypeShort(defectType)
            else:
                defectTypeId = self.putNewDefectTypeShort(defectType)

            query = ('INSERT INTO defect (findingId, type, location, evidence) '
                     'VALUES (?, ?, ?, ?)')
            self.cursor.execute(query, [str(findingId), str(defectTypeId), str(line), evidence])
            self.con.commit()
            return True

        except mdb.Error, e:
            self.error(e)

        return False

    def putNewDefectTypeShort(self, defectType):
        """ Insert a generic new type into DB. 
            The type won't have a description. Returns id.
        """
        self.cursor.execute('INSERT INTO defectType (type) VALUES (?)', [defectType])
        return self.cursor.lastrowid

    def putNewDefectType(self, defectType, description):
        """ Insert a new type with description unless already in database.
            Supposed to be used by plugins prior entering defects, so that
            proper description is available in report.
            Returns nothing.
        """
        self.cursor.execute ('SELECT count(id) FROM defectType WHERE type = "'+defectType+'"')
        row = self.cursor.fetchone()
        if row is not None:
            if row[0] is not None:
                if row[0] == 0:
                    self.cursor.execute('INSERT INTO defectType (type, description) VALUES(?,?)', [defectType, description])
    def setLink(self, transactionId, toUri):
        """ Set new link into transaction, finding and link tables.
            Return requestId if content needs to be downloaded.
            Return -1 is content is present.
        """
        try:
            reqId = self.gotLink(toUri)
            needContent = False
            if reqId == -1 : #nebyl pozadavek
                query = ('INSERT INTO transactions (method, uri, origin, '
                         'verificationStatusId) VALUES (\'GET\', ?, \'CHECKER\', ?)')
                self.cursor.execute(query, [toUri, str(DBAPI.getRequestedStatusId())])
                reqId = self.cursor.lastrowid
                needContent = True

            query = ('INSERT INTO finding (responseId) VALUES (?)')
            self.cursor.execute(query, [str(transactionId)])
            findingId = self.cursor.lastrowid

            query = ('INSERT INTO link (findingId, toUri, requestId) VALUES (?, ?, ?)')
            self.cursor.execute(query, [str(findingId), toUri, str(reqId)])
            self.con.commit()

            if needContent:
                return reqId
            else:
                return -1
        except mdb.Error, e:
            self.error(e)

        return None

    def gotLink(self, toUri):
      """ Check if transaction with GET method and uri specified is in the
          database.
          Return transaction id or -1 if not present
      """
      try:
         query = ('SELECT id FROM transactions WHERE method = \'GET\' and '
                  'uri = ? LIMIT 1')
         self.cursor.execute(query, [toUri])
         row = self.cursor.fetchone()
         if row is not None:
             if row[0] is not None:
                return row[0]
         return -1
      except mdb.Error, e:
         self.error(e)
         return -1

    @staticmethod
    def getFinishedStatusId(): # odkaz v reportu
        return 5

    @staticmethod
    def getUnverifiedStatusId(): # bere getTransaction
        return 3

    @staticmethod
    def getRequestedStatusId():
        return 1

    @staticmethod
    def getProcessingStatusId():
        return 4

    def setFinished(self, transactionId):
        """ Mark in the database that we are done with verification of a
            particular transaction.

            Return: True, if change was made, false if MySQL error occured
        """
        try:
            statusId = DBAPI.getFinishedStatusId()
            query = ('UPDATE transactions SET verificationStatusId = ? '
                     ' WHERE id = ?')
            self.cursor.execute(query, [str(statusId), str(transactionId)])

            query = ('UPDATE link SET processed = 1 WHERE requestId = '+str(transactionId)+'')
            self.cursor.execute(query)
            self.con.commit()
            return True

        except mdb.Error, e:
            self.error(e)

        return False

    def setResponse(self, reqId, uri, status, contentType, content):
        """ Set response into database.

            Return true, if transaction was updated, false otherwise.
        """
        try:
            query = ('UPDATE transactions SET responseStatus = ?, '
                     'contentType = ?, '
                     'verificationStatusId = ?, content = ? WHERE id = ?')
            self.cursor.execute(query, [str(status), contentType, str(DBAPI.getUnverifiedStatusId()), content, str(reqId)])
            self.con.commit()
            return True
        except mdb.Error, e:
            self.error(e)
            return -1


    def getUri(self, trID):
        """ Get URI for transaction ID.
        """
        try:
           query = ('SELECT uri FROM transactions WHERE id = '+str(trID))
           self.cursor.execute(query)
           row = self.cursor.fetchone()
           if row is not None:
              assert row[0] is not None
              return urllib.unquote(row[0]).decode('utf-8')
           else:
             return -1
        except mdb.Error, e:
           self.error(e)
           return -1

    def error(self, e):
        if self.con:
           self.con.rollback()
        print "Error?!? %s" % (e.args[0])
