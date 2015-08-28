require 'webrick' 
require 'webrick/httpproxy'
require 'mysql'
require 'charlock_holmes'
require_relative 'configuration'

### Webrick wrapper - content handler creates a transaction and pushes it to DB

class Transaction
  def initialize(method, uri, status, ctype, content, configuration)
    @method = method
    @uri = uri
    @status = status
    @ctype = ctype
    @content = content
    
    # Get rid of anything non-ASCII, we'll loose something, 
    # but tags are always ASCII, so only valuable thing (I can think of)
    # are some special URI's - and if someone uses those, they deserve
    # error on those ....

    # http://stackoverflow.com/questions/1268289/how-to-get-rid-of-non-ascii-characters-in-ruby
    # See String#encode
    encoding_options = {
        :invalid           => :replace,  # Replace invalid byte sequences
        :undef             => :replace,  # Replace anything not defined in ASCII
        :replace           => '',        # Use a blank for those replacements
     #  :universal_newline => true       # Always break lines with \n
    }

   # @content.encode(Encoding.find('ASCII'), encoding_options)

    #detection = CharlockHolmes::EncodingDetector.detect(content)
    #if (method == 'GET' or method == 'POST') and detection != nil and detection[:type] != :binary 
     # CharlockHolmes::Converter.convert @content, detection[:encoding], 'UTF-8'
    #puts @content
    #end
    @con = Mysql.new(configuration.getServer(), configuration.getUser(), configuration.getPassword(), configuration.getDb())
  end

  def getMySQLquery
    return @con.prepare "INSERT INTO transaction (method, uri, responseStatus, contentType, verificationStatusId, origin, content) VALUES (?, ?, ?, ?, 3, 'CLIENT', ?)"
  end

  def pushDB
    begin
      pst = getMySQLquery
      @con.query("SET NAMES UTF8")
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
