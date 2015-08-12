
class DBAPIconfiguration:
  def __init__(_self):
    _self.uri = ""
    _self.user = ""
    _self.password = ""
    _self.dbname = ""

  def getUri(_self):
    return _self.uri

  def getUser(_self):
    return _self.user

  def getPassword(_self):
    return _self.password

  def getDbname(_self):
    return _self.dbname

  def setUri(_self, uri):
    _self.uri = uri

  def setUser(_self, user):
    _self.user = user

  def setPassword(_self, pwd):
    _self.password = pwd

  def setDbname(_self, dbname):
    _self.dbname = dbname
