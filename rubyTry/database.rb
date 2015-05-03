require 'mysql'
begin
  con = Mysql.new 'localhost', '__name__', '***'
  con.list_dbs.each do |db|
    puts db
  end

rescue Mysql::Error => e
  puts e.errno
  puts e.error
   
ensure
  con.close if con
end

class Database
  def initialize(dbserver, userName, password, dbName)
    @connection = Mysql.new (dbserver, userName, password, dbName)
    
  end

  def storeURIfromProxy(uri)
    
  end

  def getURIfromDB()
    return false
  end

  def setValid(uri)
  end

  def setFinding(type, uri, line, col, message)
  end
end
