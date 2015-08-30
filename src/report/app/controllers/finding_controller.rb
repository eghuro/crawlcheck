require 'active_record/errors'
class FindingController < ApplicationController
  helper_method :getDefectDescription

  def show
    @empty = true
    begin
      @transaction = Transaction.find(params[:id])
      @finding = Finding.find_by responseId: params[:id]
      if @finding
        @findingId = @finding.id
        Rails.logger.debug("#{@finding.id}")
        @defects = Defect.find_by_sql("select * from defect where findingId in (select id from finding where responseId = #{params[:id]})")
        @links = Link.find_by_sql("select * from link where findingId in (select id from finding where responseId = #{params[:id]})")

      end
    rescue ActiveRecord::RecordNotFound
    end
  end

  def getDefectDescription(id)
    @dType = Dtype.find(id)
    return @dType.description
  end
end
