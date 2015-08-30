require 'nokogiri'
require 'open-uri'

class ProxyConfigurationParser
  def self.parse(config_file)
    puts "Parsing: #{config_file}"
    f = File.open(config_file)
    doc = Nokogiri::XML(f)
    user = doc.xpath("//db/@user").text
    password = doc.xpath("//db/@pass").text
    dbname = doc.xpath("//db/@dbname").text
    server = doc.xpath("//db/@uri").text
    port = doc.xpath("//proxy/@inPort").text

    return ProxyConfiguration.create(server, user, password, dbname, port)
  end
end

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
