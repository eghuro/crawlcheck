require 'webrick'
require 'webrick/httpproxy'

class UserAgent
  def initialize(port)
    uris = []
    contents = []

    @database = Database.new('','','','')

    @server = WEBrick::HTTPProxyServer.new Port: port, ProxyContentHandler: getHandler(uris)

    trap 'INT' do
      @server.shutdown
      shutdown(uris)   
    end
    trap 'TERM' do 
      @server.shutdown
      shutdown(uris) 
    end

    @server.start
  end

  def getHandler (uris)
    return Proc.new{|req,res| 
     if response_filter(res)
       @database.storeURIfromProxy(res.request_uri)
       uris.push(res.request_uri)
     end
    }
  end

  def shutdown(uris)
    puts "SHUTDOWN routine"

    puts "Captured URIs"
    for uri in uris
      puts uri,"\n"
    end

    exit
  end

  def response_filter(res)
     if ['GET', 'POST'].include?(res.request_method)
       if res.content_type().include? 'text/html'
         return true
       end
     end
     return false
  end
end


ua = UserAgent.new(1234)
