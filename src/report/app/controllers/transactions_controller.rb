class TransactionsController < ApplicationController
  def index
    @transactions = Transaction.all
    @status = Status.all
  end
end
