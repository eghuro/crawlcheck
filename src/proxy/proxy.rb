require 'webrick' 
require 'webrick/httpproxy'
require 'mysql'
require_relative 'configuration'

### Webrick wrapper - content handler creates a transaction and pushes it to DB

class Transaction
  def initialize(method, uri, status, ctype, content, configuration)
    @method = method
    @uri = uri
    @status = status
    @ctype = ctype
    @content = content

    @con = Mysql.new(configuration.getServer(), configuration.getUser(), configuration.getPassword(), configuration.getDb())
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

# Content handler - prepare a transaction and push it to the database
class Handler
  def initialize (conf)
    @conf = conf
  end

  def handle_content (req, res)
     trans = Transaction.new(req.request_method(), req.unparsed_uri(), res.status, res.content_type(), res.body, @conf)
     trans.pushDB
  end
end

# Parse configuration
conf = ProxyConfigurationParser.parse(ARGV[0])

# Prepare handler
proxy = Handler.new(conf)

# Preoare webrick
s = WEBrick::HTTPProxyServer.new(:Port => conf.getPort(), :ProxyContentHandler => proxy.method(:handle_content))

# Shutdown functionality
trap("INT"){s.shutdown}

# Eun the beast
s.start
