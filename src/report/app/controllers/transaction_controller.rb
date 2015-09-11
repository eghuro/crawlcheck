require 'uri'
require 'will_paginate'

class TransactionController < ApplicationController
  helper_method :format
  def index
    @transactions = Transaction.all.order('uri ASC').paginate(page: params[:page], per_page: 25)
    @status = Status.all
  end

  def format(uri)
    return URI.unescape(uri)
  end
end
