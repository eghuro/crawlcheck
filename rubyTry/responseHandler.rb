class ResponseHandler < WEBrick::HTTPServlet::AbstractServlet
  def do_GET request, response
    process response
  end

  def process response
    puts response.body
  end
end
