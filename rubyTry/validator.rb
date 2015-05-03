class Validator
  require 'w3c_validators'

  include W3CValidators

  def initialize
    @validator = MarkupValidator.new

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
      end
    else
      puts 'Valid!'
    end
  end
end

@validator = Validator.new
@validator.validate('http://www.mff.cuni.cz')
