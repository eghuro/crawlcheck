require 'uri'

class TransactionController < ApplicationController
  helper_method :format
  def index
    @transactions = Transaction.all.order('uri ASC')
    @status = Status.all
  end

  def format(uri)
    return URI.unescape(uri)
  end
end
