require 'active_record/errors'
class FindingController < ApplicationController
  def show
    @empty = true
    begin
      @transaction = Transaction.find(params[:id])
      @finding = Finding.find_by responseId: params[:id]
      if @finding
        @findingId = @finding.id
        Rails.logger.debug("#{@finding.id}")
        @defects = Defect.where(findingId = @findingId).all
        @links = Link.where(findingId = @findingId).all
      end
    rescue ActiveRecord::RecordNotFound
    end
  end
end
