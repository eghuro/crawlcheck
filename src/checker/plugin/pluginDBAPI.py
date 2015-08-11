import MySQLdb as mdb

class DBAPI:
  def __init__(_self, conf):
    _self.con = mdb.connect(conf.getUri(), conf.getUser(), conf.getPassword(), conf.getDbname())
    _self.cursor = _self.con.cursor()

  def __del__(_self):
    if _self.con:
      _self.con.close()

  def getTransactionId(_self):
    print "getTransaction";
    transactionId = -1;
    # SELECT & UPDATE
    _self.cursor.execute("START TRANSACTION")
    _self.cursor.execute("SELECT @A:=MAX(transaction.id), content FROM transaction INNER JOIN verificationStatus ON verificationStatus.id = transaction.id WHERE transaction.responseStatus = 200 AND transaction.contentType = \"text/html\" AND transaction.method = 'GET' AND verificationStatus.status = \"UNVERIFIED\"")
    row = _self.cursor.fetchone()
    if row is not None:
      if row[0] is not None:
        transactionId = row[0]
        print transactionId
        assert row[1] is not None
        content = row[1]
        _self.cursor.execute("UPDATE transaction SET verificationStatusId = (SELECT id FROM verificationStatus WHERE status = \"PROCESSING\") WHERE id = @A")
    _self.cursor.execute("COMMIT")
    return transactionId;

  def setDefect(_self, tranactionId, defectType, line, evidence):
    return False;

  def setLink(_self, transactionId, toUri):
    return False;

  def setFinished(_self, transactionId, status):
    return False;
