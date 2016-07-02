require 'active_record/errors'
require 'uri'
require 'will_paginate'

class FindingController < ApplicationController
  helper_method :getDefectDescription
  helper_method :format
  helper_method :getTypes

  def index
    defect_query = "select transactions.uri, location, evidence, defectType.description, finding.responseId as responseId from defect inner join finding on finding.id = defect.findingId inner join defectType on defect.type = defectType.id inner join transactions on transactions.id = finding.responseId "
    if params.has_key?("d")
      @filtered = true
      defect_query += "where defect.type = "+params[:d]+" "
    end
    defect_query += "order by defectType.type"
    link_query = "select distinct uri, toUri, processed from link inner join finding on finding.id = link.findingId inner join transactions on finding.responseId = transactions.id order by toUri"
    @defects = Defect.paginate_by_sql(defect_query, page: params[:defect], per_page: 25)
    @links = Link.paginate_by_sql(link_query, page: params[:link], per_page: 25)
  end

  def show
    begin
      @transaction = Transaction.find(params[:id])
      @defects = Defect.paginate_by_sql("select * from defect where findingId in (select id from finding where responseId = #{params[:id]})", page: params[:defect], per_page: 25)
      @links = Link.paginate_by_sql("select * from link where findingId in (select id from finding where responseId = #{params[:id]})", page: params[:link], per_page: 25)
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

  def getTypes
    return Dtype.select(:id, :description).distinct
  end
end
