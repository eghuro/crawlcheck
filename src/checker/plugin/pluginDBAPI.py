import MySQLdb as mdb

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
  def __init__(_self, conf):
    _self.con = mdb.connect(conf.getUri(), conf.getUser(), conf.getPassword(), conf.getDbname())
    _self.cursor = _self.con.cursor()

  def __del__(_self):
    if _self.con:
      _self.con.close()

  def getTransaction(_self):
    transactionId = -1;
    content = ""

    try:
      _self.cursor.execute("SELECT @A:=MAX(transaction.id), content FROM transaction INNER JOIN verificationStatus ON verificationStatus.id = transaction.id WHERE transaction.responseStatus = 200 AND transaction.contentType = \"text/html\" AND transaction.method = 'GET' AND verificationStatus.status = \"UNVERIFIED\"")
      row = _self.cursor.fetchone()
      if row is not None:
        if row[0] is not None:
          transactionId = row[0]
          print transactionId
          assert row[1] is not None
          content = row[1]
          _self.cursor.execute("UPDATE transaction SET verificationStatusId = (SELECT id FROM verificationStatus WHERE status = \"PROCESSING\") WHERE id = @A")
      _self.con.commit()

    except mdb.Error, e:
      if _self.con:
        _self.con.rollback()
      print "Error %d: %s" % (e.args[0],e.args[1])

    return TransactionInfo(transactionId, content);

  def setDefect(_self, transactionId, defectType, line, evidence):
    try:
      _self.cursor.execute("INSERT INTO finding (responseId) VALUES (" + str(transactionId)+ ")")
      findingId = _self.cursor.lastrowid
      #_self.cursor.execute("SELECT id FROM defectType WHERE type = " + str(defectType))
      #row = _self.cursor.fetchone()
      #if row is not None:
        #if row[0] is not None:
          #defectTypeId = _self.cursor.fetchone()[0]
      defectTypeId = defectType
      _self.cursor.execute("INSERT INTO defect (findingId, type, location, evidence) VALUES (" + str(findingId) + ", " + str(defectTypeId) + ", " + str(line) + ", \"" + _self.con.escape_string(evidence) + "\" )")
      _self.con.commit()
      return True
     #   else:
     #     _self.con.rollback()
     #     return False
     # else:
     #   _self.con.rollback()
     #   return False

    except mdb.Error, e:
      if _self.con:
        _self.con.rollback()
      print "Error %d: %s" % (e.args[0],e.args[1]) 
      return False

  def setLink(_self, transactionId, toUri):
    try:
      _self.cursor.execute("INSERT INTO finding (responseId) VALUES (" + str(transactionId) + ")")
      findingId = _self.cursor.lastrowid
      _self.cursor.execute("INSERT INTO link (findingId, toUri) VALUES (" + str(findingId) + ", " + _self.con.escape_string(toUri) + ")")

    except mdb.Error, e:
      if _self.con:
        _self.con.rollback()
      print "Error %d: %s" % (e.args[0],e.args[1])
      return False

  def setFinished(_self, transactionId, status):
    try:
      _self.cursor.execute("UPDATE transaction SET verificationStatusId = " + str(statusId) + " WHERE id = " + str(transactionId))
      _self.con.commit()
      return True

    except mdb.Error, e:
      if _self.con():
        _self.con.rollback()
        print "Error %d: %s" % (e.args[0],e.args[1])
        return False
