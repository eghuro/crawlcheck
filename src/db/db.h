// Copyright 2015 Alexandr Mansurov

#ifndef SRC_DB_DB_H_
#define SRC_DB_DB_H_

#include <cassert>
#include <sstream>
#include <mysql_connection.h>
#include "mysql_driver.h"
#include "cppconn/driver.h"
#include "cppconn/exception.h"
#include "cppconn/resultset.h"
#include "cppconn/statement.h"
#include "cppconn/prepared_statement.h"
#include "../proxy/HttpParser.h"
#include "../proxy/HelperRoutines.h"

class DatabaseConfiguration {
 public:
  DatabaseConfiguration():uri(), user(), pwd() {}

  void setUri(const std::string & newUri) {
    uri = newUri;
  }
  void setUser(const std::string & newUser) {
    user = newUser;
  }
  void setPass(const std::string & pass) {
    pwd = pass;
  }

  void setDb(const std::string & db) {
    database = db;
  }

  std::string getUri() const {
    return uri;
  }
  std::string getUser() const {
    return user;
  }
  std::string getPass() const {
    return pwd;
  }

  std::string getDb() const {
    return database;
  }
 private:
  std::string uri, user, pwd, database;
};

class Database{
 public:
  typedef std::size_t TransactionIdentifier;

  Database(const DatabaseConfiguration& dbc):config(dbc) {
    driver = get_driver_instance();
    con = driver->connect(dbc.getUri(), dbc.getUser(), dbc.getPass());
    con -> setSchema(dbc.getDb());
  }

  virtual ~Database() {
    delete con;
  }

  std::size_t getClientRequestCount() {
    sql::Statement *stmt = con->createStatement();

    sql::ResultSet *res = stmt->executeQuery("SELECT count(id) AS id FROM transaction WHERE verificationStatusId= 1");

    unsigned int count = 0;
    if (res->next()) {
      count = res->getUInt("id");
    }
    delete stmt;
    delete res;
    return count;
  }

  TransactionIdentifier setClientRequest(const HttpParserResult & request) {
    assert(request.isRequest());

    std::ostringstream oss;
    oss << "INSERT INTO transaction (uri, method, verificationStatusId) VALUES (\"";
    oss << request.getRequestUri().getUri();
    oss << "\", '";
    oss << RequestMethodTransformer::toString(request.getMethod());
    oss << "', 1)";

    auto *stmt = con->createStatement();
    int count = stmt->executeUpdate(oss.str());

    delete stmt;

    unsigned int id = 0;
    if (count > 0) {
      stmt = con->createStatement();
      sql::ResultSet *res = stmt->executeQuery("SELECT LAST_INSERT_ID() AS id");
      if (res->next()) {
        id = res->getUInt("id");
      }
      delete res;
      delete stmt;
    }

    return id;
  }

  HttpParserResult getClientRequest(const TransactionIdentifier & identifier) {
    std::ostringstream oss;
    oss << "SELECT method, uri FROM transaction WHERE id = ";
    oss << identifier;

    auto *stmt = con->createStatement();
    sql::ResultSet *res = stmt->executeQuery(oss.str());

    if (res->next()) {
      HttpParserResult ret(HttpParserResultState::REQUEST);
      ret.setMethod(RequestMethodTransformer::transformMethod(res->getString("method")));
      ret.setRequestUri(HttpUriFactory::createUri(res->getString("uri")));

      delete stmt;
      delete res;
      return ret;
    } else {

      delete stmt;
      delete res;
      return HttpParserResult(HttpParserResultState::REQUEST);
    }
  }

  std::size_t getServerResponseCount() {
    sql::Statement *stmt = con->createStatement();

    sql::ResultSet *res = stmt->executeQuery("SELECT count(id) AS id FROM transaction WHERE verificationStatusId= 3");

    unsigned int count = 0;
    if (res->next()) {
      count = res->getUInt("id");
    }
    delete stmt;
    delete res;
    return count;
  }

  void setServerResponse(const TransactionIdentifier tid, const HttpParserResult & response) {
    assert(response.isResponse());

    sql::mysql::MySQL_Connection * mysql_conn = dynamic_cast<sql::mysql::MySQL_Connection*>(con);
    std::string escapedContent = mysql_conn->escapeString( response.getContent() );

    std::ostringstream oss;
    oss << "UPDATE transaction SET responseStatus = \"";
    oss << response.getStatus().getCode();
    oss << "\", contentType = \"" << response.getContentType() << "\", ";
    oss <<  "content = \"" << escapedContent << "\", ";
    oss << "verificationStatusId = 3 WHERE id = " << tid;

    auto *stmt = con->createStatement();
    stmt->executeUpdate(oss.str());

    delete stmt;
  }

  HttpParserResult getServerResponse(const TransactionIdentifier & identifier) {
    std::ostringstream oss;
    oss << "SELECT responseStatus, contentType, content FROM transaction ";
    oss << "WHERE id = " << identifier;

    auto *stmt = con -> createStatement();
    sql::ResultSet *res = stmt->executeQuery(oss.str());

    if (res->next()) {
      HttpParserResult ret(HttpParserResultState::RESPONSE);
      ret.setResponseStatus(HttpResponseStatus(res->getUInt("responseStatus")));
      ret.setContentType(res->getString("contentType"));
      ret.setContent(res->getString("content"));

      delete stmt;
      delete res;
      return ret;
    } else {
      delete stmt;
      delete res;
      return HttpParserResult(HttpParserResultState::RESPONSE);
    }
  }

 private:
  const DatabaseConfiguration & config;
  sql::Driver *driver;
  sql::Connection *con;
};

#endif  // SRC_DB_DB_H_
