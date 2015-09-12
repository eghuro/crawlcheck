require 'uri'
require 'will_paginate'

class TransactionController < ApplicationController
  helper_method :format
  helper_method :getStatuses
  def index
    if params.has_key?("s")
      @filtered = true
      @transactions = Transaction.where(verificationStatusId: params[:s]).order('uri ASC').paginate(page: params[:page], per_page: 25)
    else
      @transactions = Transaction.all.order('uri ASC').paginate(page: params[:page], per_page: 25)
    end
    @status = Status.all
  end

  def format(uri)
    return URI.unescape(uri)
  end

  def getStatuses
    return Status.find_by_sql("select distinct verificationStatus.id, status from verificationStatus inner join transactions on verificationStatus.id = transactions.verificationStatusId order by status ASC")
  end
end
