class TransactionController < ApplicationController
  def index
    @transactions = Transaction.all.order('uri ASC')
    @status = Status.all
  end
end
