class Dtype < ActiveRecord::Base
  self.table_name = "defectType"

  private

    def self.inheritance_column
      nil
    end
end
