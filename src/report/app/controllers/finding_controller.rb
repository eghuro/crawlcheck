require 'active_record/errors'
require 'uri'

class FindingController < ApplicationController
  helper_method :getDefectDescription
  helper_method :format

  def index
    @defects = Defect.find_by_sql("select transaction.uri, location, evidence, defectType.description from defect inner join finding on finding.id = defect.findingId inner join defectType on defect.type = defectType.id inner join transaction on transaction.id = finding.responseId order by defectType.type")
    @links = Link.find_by_sql("select distinct uri, toUri, processed from link inner join finding on finding.id = link.findingId inner join transaction on finding.responseId = transaction.id order by toUri")
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

  def format(uri)
    return URI.unescape(uri)
  end
end
