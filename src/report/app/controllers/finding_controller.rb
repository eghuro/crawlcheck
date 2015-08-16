require 'active_record/errors'
class FindingController < ApplicationController
  def show
    @empty = true
    begin
      @transaction = Transaction.find(params[:id])
      @finding = Finding.find(:first, :conditions => ["responseId = ?", params[:id]])
      @findingId = @finding.id
      @defects = Defect.find(:all, @findingId)
      @links = Link.find(:all, @findingId)
      @empty = false
    rescue ActiveRecord::RecordNotFound
    end
  end
end
