require 'webrick' 
require 'webrick/httpproxy'
require 'mysql'

class Transaction
  def initialize(method, uri, status, ctype, content)
    @method = method
    @uri = uri
    @status = status
    @ctype = ctype
    @content = content

    @con = Mysql.new 'localhost', 'test', '', 'crawlcheck'
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
  trans = Transaction.new(req.request_method(), req.unparsed_uri(), res.status, res.content_type(), res.body)
  trans.pushDB
end

s = WEBrick::HTTPProxyServer.new(:Port => 8080, :ProxyContentHandler => method(:handle_content))

# Shutdown functionality
trap("INT"){s.shutdown}

# # run the beast
s.start
