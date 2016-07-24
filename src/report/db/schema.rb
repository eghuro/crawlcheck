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

ActiveRecord::Schema.define(version: 1) do

  create_table "HTTPmethods", primary_key: "method", force: :cascade do |t|
  end

  add_index "HTTPmethods", ["method"], name: "sqlite_autoindex_HTTPmethods_1", unique: true

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

  add_index "defect", ["type"], name: "type"

  create_table "defectType", force: :cascade do |t|
    t.string "type",        limit: 255,   null: false
    t.text   "description", limit: 65535
  end

  create_table "finding", force: :cascade do |t|
    t.integer "responseId", limit: 4, null: false
  end

  add_index "finding", ["responseId"], name: "responseId"

  create_table "link", primary_key: "findingId", force: :cascade do |t|
    t.string  "toUri",     limit: 255,                 null: false
    t.boolean "processed",             default: false, null: false
    t.integer "requestId", limit: 4
  end

  add_index "link", ["requestId"], name: "requestId"

  create_table "parameter", force: :cascade do |t|
    t.string "uri",  limit: 255, null: false
    t.string "name", limit: 255, null: false
  end

  create_table "parameterValue", primary_key: "findingId", force: :cascade do |t|
    t.string "value", limit: 255, null: false
  end

  create_table "scriptAction", primary_key: "findingId", force: :cascade do |t|
    t.integer "parameterId",            null: false
    t.string  "method",      limit: 10, null: false
  end

  create_table "transaction", force: :cascade do |t|
    t.string  "method",               limit: 7,     null: false
    t.string  "uri",                  limit: 255,   null: false
    t.integer "responseStatus",       limit: 4
    t.string  "contentType",          limit: 255
    t.text    "content",              limit: 65535
    t.integer "verificationStatusId", limit: 4
    t.string  "origin",               limit: 7
    t.binary  "rawRequest"
    t.binary  "rawResponse"
  end

  add_index "transaction", ["verificationStatusId"], name: "verificationStatusId"

  create_table "transactions", force: :cascade do |t|
    t.string  "method",               limit: 10,  null: false
    t.string  "uri",                  limit: 255, null: false
    t.integer "responseStatus"
    t.string  "contentType",          limit: 255
    t.text    "content"
    t.integer "verificationStatusId"
    t.string  "origin",               limit: 255
    t.integer "depth",                            null: false
  end

  create_table "verificationStatus", force: :cascade do |t|
    t.string "status",      limit: 255,   null: false
    t.text   "description", limit: 65535
  end

end
