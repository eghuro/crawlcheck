require 'active_record/errors'
class FindingController < ApplicationController
  helper_method :getDefectDescription

  def index
    @defects = Defect.find_by_sql("select transaction.uri, location, evidence, defectType.description from defect inner join finding on finding.id = defect.findingId inner join defectType on defect.type = defectType.id inner join transaction on transaction.id = finding.responseId order by uri")
    @links = Link.find_by_sql("select uri, toUri, processed from link join finding on finding.id = link.findingId join transaction on finding.responseId = transaction.id order by uri")
  end

  def show
    begin
      @transaction = Transaction.find(params[:id])
      @defects = Defect.find_by_sql("select * from defect where findingId in (select id from finding where responseId = #{params[:id]})")
      @links = Link.find_by_sql("select * from link where findingId in (select id from finding where responseId = #{params[:id]})")
    rescue ActiveRecord::RecordNotFound
    end
  end

  def getDefectDescription(id)
    @dType = Dtype.find(id)
    return @dType.description
  end
end
