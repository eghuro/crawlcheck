class Defect < ActiveRecord::Base
  private
    def self.inheritance_column
      nil
    end
end
