require 'webrick' 
require 'webrick/httpproxy'
require 'mysql'
#require 'iconv'

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
      #con = Mysql.new('localhost', 'test', '', 'crawlcheck')

      pst = getMySQLquery
      pst.execute @method, @uri, @status, @ctype, @content 

    rescue Mysql::Error => e
      puts e.errno
      puts e.error
    end
  end
end

#ic = Iconv.new('UTF-8//IGNORE', 'UTF-8')

def handle_content (req, res)
  #ic = Iconv.new('UTF-8//IGNORE', 'UTF-8')

  trans = Transaction.new(req.request_method(), req.unparsed_uri(), res.status, res.content_type(), res.body)
  #puts trans.getMySQLquery()
  trans.pushDB

  #puts "Method: ", req.request_method()
  #puts "Uri: ", req.unparsed_uri()

  #puts "Content-type: ", res.content_type()
  #puts "Response status: ", res.status
  #puts "Content: ",ic.iconv(res.body)
end

s = WEBrick::HTTPProxyServer.new(:Port => 8080, :ProxyContentHandler => method(:handle_content))

# Shutdown functionality
trap("INT"){s.shutdown}

# # run the beast
s.start
