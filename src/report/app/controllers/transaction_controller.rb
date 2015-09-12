require 'uri'
require 'will_paginate'

class TransactionController < ApplicationController
  helper_method :format
  helper_method :getStatuses
  helper_method :getTypes
  helper_method :escape
  helper_method :addToUri

  def index
    t = Transaction.all

    if params.has_key?("s")
      @filtered1 = true
      unesc = format params[:s]
      t = t.where(verificationStatusId: unesc)
    end

    if params.has_key?("t")
      @filtered2 = true
      t = t.where(contentType: params[:t])
    end

    @transactions = t.order('uri ASC').paginate(page: params[:page], per_page: 25)
    @status = Status.all
  end

  def format(uri)
    return URI.unescape(uri)
  end

  def getStatuses
    return Status.find_by_sql("select distinct verificationStatus.id, status from verificationStatus inner join transactions on verificationStatus.id = transactions.verificationStatusId order by status ASC")
  end

  def getTypes
    return Transaction.find_by_sql("select distinct contentType from transactions order by contentType ASC")
  end

  def escape(type)
    return ERB::Util.url_encode type
  end

  def addToUri(param, value)
    if params.has_key?("s") && param != "s"
      return "?s="+params[:s]+"&"+param+"="+value
    elsif params.has_key?("p") && param != "p"
      return "?p="+params[:p]+"&"+param+"="+value
    else
      return "?"+param+"="+value.to_s
    end
  end
end
