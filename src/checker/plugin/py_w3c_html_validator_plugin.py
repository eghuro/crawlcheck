
from py_w3c.validators.html.validator import HTMLValidator

class PyW3C_HTML_Validator:
  def __init__(_self, DB):
    _self.validator = HTMLValidator()
    _self.database = DB
  
  def check(_self, transactionId, content): 
    _self.validator.validate_fragment(content)
    # print _self.validator.errors
    for error in _self.validator.errors:
      _self.database.setDefect(transactionId, error['messageid'], error['line'], error['source'])

      print _self.validator.warnings
    return
