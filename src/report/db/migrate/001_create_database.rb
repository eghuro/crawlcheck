# encoding: UTF-8
# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# Note that this schema.rb definition is the authoritative source for your
# database schema. If you need to create the application database on another
# system, you should be using db:schema:load, not running all the migrations
# from scratch. The latter is a flawed and unsustainable approach (the more migrations
# you'll amass, the slower it'll run and the greater likelihood for issues).
#
# It's strongly recommended that you check this file into your version control system.
class CreateDatabase < ActiveRecord::Migration
  def self.up
    ActiveRecord::Schema.define(version: 0) do

      create_table "annotation", force: :cascade do |t|
        t.integer  "findingId", limit: 4,     null: false
        t.text     "comment",   limit: 65535, null: false
        t.string   "author",    limit: 255,   null: false
        t.datetime "created",                 null: false
      end

      create_table "defect", primary_key: "findingId", force: :cascade do |t|
        t.integer "type",     limit: 4,     null: false
        t.integer "location", limit: 4,     null: false
        t.text    "evidence", limit: 65535, null: false
      end

      add_index "defect", ["type"], name: "type", using: :btree

      create_table "defectType", force: :cascade do |t|
        t.string "type",        limit: 255,   null: false
        t.text   "description", limit: 65535
      end

      create_table "finding", force: :cascade do |t|
        t.integer "responseId", limit: 4, null: false
      end

      add_index "finding", ["responseId"], name: "responseId", using: :btree

      create_table "link", primary_key: "findingId", force: :cascade do |t|
        t.string  "toUri",     limit: 255,                 null: false
        t.boolean "processed",             default: false, null: false
        t.integer "requestId", limit: 4
      end

      add_index "link", ["requestId"], name: "requestId", using: :btree

      create_table "transaction", force: :cascade do |t|
        t.string  "method",               limit: 7,     null: false
        t.string  "uri",                  limit: 255,   null: false
        t.integer "responseStatus",       limit: 4
        t.string  "contentType",          limit: 255
        t.text    "content",              limit: 65535
        t.integer "verificationStatusId", limit: 4
        t.string  "origin",               limit: 7
        t.binary  "rawRequest",           limit: 65535
        t.binary  "rawResponse",          limit: 65535
      end

      add_index "transaction", ["verificationStatusId"], name: "verificationStatusId", using: :btree

      create_table "verificationStatus", force: :cascade do |t|
        t.string "status",      limit: 255,   null: false
        t.text   "description", limit: 65535
      end

      add_foreign_key "defect", "defectType", column: "type", name: "defect_ibfk_2", on_delete: :cascade
      add_foreign_key "defect", "finding", column: "findingId", name: "defect_ibfk_1", on_delete: :cascade
      add_foreign_key "finding", "transaction", column: "responseId", name: "finding_ibfk_1", on_delete: :cascade
      add_foreign_key "link", "finding", column: "findingId", name: "link_ibfk_1", on_delete: :cascade
      add_foreign_key "link", "transaction", column: "requestId", name: "link_ibfk_2", on_delete: :cascade
      add_foreign_key "transaction", "verificationStatus", column: "verificationStatusId", name: "transaction_ibfk_1", on_delete: :cascade
    end
  end

  def self.down
  end
end
