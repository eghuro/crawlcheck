class TransactionController < ApplicationController
  def index
    @transactions = Transaction.all
    @status = Status.all
  end

  def show
    @transaction = Transaction.find(params[:id])
    render layout: false
    # render status: @transaction.responseStatus, content_type: @transaction.contentType, raw: @transaction.content
  end
end
