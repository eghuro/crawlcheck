require 'webrick' 
require 'webrick/httpproxy'
require 'mysql'

class ProxyConfiguration
  def initialize
    @server = ''
    @user = ''
    @pass = ''
    @dbname = ''
    @port = -1
  end

  def setServer(name)
    @server = name
  end

  def getServer
    return @server
  end

  def setUser(user)
    @user = user
  end

  def getUser
    return @user
  end

  def setPassword(pass)
    @pass = pass
  end

  def getPassword
    return @pass
  end

  def setDb(name)
    @dbname = name
  end

  def getDb
    return @dbname
  end

  def setPort(port)
    @port = port
  end

  def getPort
    return @port
  end

  def self.create(server, user, pass, dbname, port)
    conf = ProxyConfiguration.new
    conf.setServer(server)
    conf.setUser(user)
    conf.setPassword(pass)
    conf.setDb(dbname)
    conf.setPort(port)
    return conf
  end
end

class Transaction
  def initialize(method, uri, status, ctype, content, configuration)
    @method = method
    @uri = uri
    @status = status
    @ctype = ctype
    @content = content

    @con = Mysql.new(configuration.getDb(), configuration.getUser(), configuration.getPassword(), configuration.getDb())
  end

  def getMySQLquery
    return @con.prepare "INSERT INTO transaction (method, uri, responseStatus, contentType, verificationStatusId, origin, content) VALUES (?, ?, ?, ?, 3, 'CLIENT', ?)"
  end

  def pushDB
    begin
      pst = getMySQLquery
      pst.execute @method, @uri, @status, @ctype, @content 

    rescue Mysql::Error => e
      puts e.errno
      puts e.error
    end
  end
end

def handle_content (req, res)
  trans = Transaction.new(req.request_method(), req.unparsed_uri(), res.status, res.content_type(), res.body, conf)
  trans.pushDB
end


conf = ProxyConfiguration.create('localhost', 'test', '', 'crawlcheck', 8080)
s = WEBrick::HTTPProxyServer.new(:Port => conf.getPort(), :ProxyContentHandler => method(:handle_content))

# Shutdown functionality
trap("INT"){s.shutdown}

# # run the beast
s.start
