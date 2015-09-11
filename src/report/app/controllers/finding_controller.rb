require 'active_record/errors'
require 'uri'
require 'will_paginate'

class FindingController < ApplicationController
  helper_method :getDefectDescription
  helper_method :format

  def index
    defect_query = "select transactions.uri, location, evidence, defectType.description from defect inner join finding on finding.id = defect.findingId inner join defectType on defect.type = defectType.id inner join transactions on transactions.id = finding.responseId order by defectType.type"
    @defects = Defect.find_by_sql(defect_query)
    @links = Link.find_by_sql("select distinct uri, toUri, processed from link inner join finding on finding.id = link.findingId inner join transactions on finding.responseId = transactions.id order by toUri")
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
