class Validator
  require 'w3c_validators'

  include W3CValidators

  def initialize(db)
    @validator = MarkupValidator.new
    @database = db

    # override the DOCTYPE
    @validator.set_doctype!(:html32)

    # turn on debugging messages
    @validator.set_debug!(true)
  end

  def validate(uri)
    results = @validator.validate_uri(uri)

    if results.errors.length > 0
      results.errors.each do |err|
        puts err.to_s
        setFinding(err.:type, uri, err.:line, err.:col, err.:message)
      end
    else
      puts 'Valid!'
      @database.setValid(uri)
    end
  end
end

@validator = Validator.new
@db = Database.new('','','','')
uri = @db.getUriFromDB()
while uri != false
 @validator.validate(uri)
 uri = @db.getUriFromDB()
end
