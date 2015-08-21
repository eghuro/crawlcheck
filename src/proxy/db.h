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
#include "HttpParser.h"
#include "HelperRoutines.h"

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
    HelperRoutines::info("New DB");
    try {
      HelperRoutines::info("Get driver");
      driver = get_driver_instance();
      HelperRoutines::info("Connect");
      con = driver->connect(dbc.getUri(), dbc.getUser(), dbc.getPass());
      con -> setSchema(dbc.getDb());
      std::cout << "Connected" << std::endl;
    } catch (const sql::SQLException& ex) {
      std::ostringstream oss;
      oss << "Database connector: " << ex.what() << " (MySQL error code: " << ex.getErrorCode();
      oss << ", SQLState: " << ex.getSQLState() << " )";
      HelperRoutines::warning(oss.str());
    }
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
      HelperRoutines::info(HelperRoutines::to_string(count));
    }
    delete stmt;
    delete res;
    return count;
  }

  TransactionIdentifier setClientRequest(const HttpParserResult & request) {
    assert(request.isRequest());

    std::ostringstream oss;
    oss << "INSERT INTO transaction (uri, method, verificationStatusId, origin, rawRequest) VALUES (\"";
    oss << request.getRequestUri().getUri();
    oss << "\", '";
    oss << RequestMethodTransformer::toString(request.getMethod());
    oss << "', 1, 'CLIENT', \"";
    oss << request.getRaw();
    oss << "\")";

    con->setAutoCommit(0);
    auto *stmt = con->createStatement();
    int count = stmt->executeUpdate(oss.str());

    //delete stmt;

    unsigned int id = 0;
    if (count > 0) {
      //stmt = con->createStatement();
      sql::ResultSet *res = stmt->executeQuery("SELECT LAST_INSERT_ID() AS id");
      if (res->next()) {
        id = res->getUInt("id");
      }
      delete res;
    }
    delete stmt;
    con->setAutoCommit(1);

    return id;
  }

  HttpParserResult getClientRequest(const TransactionIdentifier & identifier) {
    std::ostringstream oss;
    oss << "SELECT method, uri, rawRequest as raw FROM transaction WHERE id = ";
    oss << identifier;

    auto *stmt = con->createStatement();
    sql::ResultSet *res = stmt->executeQuery(oss.str());

    if (res->next()) {
      HttpParserResult ret(HttpParserResultState::REQUEST);
      ret.setMethod(RequestMethodTransformer::transformMethod(res->getString("method")));
      ret.setRequestUri(HttpUriFactory::createUri(res->getString("uri")));
      ret.setRaw(res->getString("raw"));

      delete stmt;
      delete res;
      return ret;
    } else {

      delete stmt;
      delete res;
      return HttpParserResult(HttpParserResultState::INVALID);
    }
  }

  std::pair<HttpParserResult, std::size_t> getClientRequest() {
    const std::string query("SELECT id, method, uri, rawRequest as raw FROM transaction WHERE verificationStatusId = 1 LIMIT 1");
    HelperRoutines::info("Get client request");
    HelperRoutines::info(query);

    con->setAutoCommit(0);

    std::size_t id = 0;
    auto *stmt = con->createStatement();
    sql::ResultSet *res = stmt->executeQuery(query);
    if (res->next()) {
      HttpParserResult ret(HttpParserResultState::REQUEST);
      ret.setMethod(RequestMethodTransformer::transformMethod(res->getString("method")));
      ret.setRequestUri(HttpUriFactory::createUri(res->getString("uri")));
      ret.setRaw(res->getString("raw"));

      id = res->getUInt("id");

      HelperRoutines::info(res->getString("method"));
      HelperRoutines::info(res->getString("uri"));
      HelperRoutines::info(res->getString("raw"));
      HelperRoutines::info(HelperRoutines::to_string(res->getUInt("id")));

      delete stmt;
      delete res;

      stmt = con->createStatement();
      std::ostringstream oss;
      oss << "UPDATE transaction SET verificationStatusId = 2 WHERE id = " << id;

      if (stmt->executeUpdate(oss.str()) == 1) {
        con->commit();
        con->setAutoCommit(1);
        return std::pair<HttpParserResult, std::size_t>(ret, id);
      } else {
        con->rollback();
      }
    }
    con->setAutoCommit(1);
    return std::pair<HttpParserResult, std::size_t>(HttpParserResult(HttpParserResultState::INVALID), 0);
  }

  std::size_t getServerResponseCount() {
    sql::Statement *stmt = con->createStatement();

    sql::ResultSet *res = stmt->executeQuery("SELECT count(id) AS id FROM transaction WHERE verificationStatusId = 3 AND origin='CLIENT'");

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
    std::string escapedRaw = mysql_conn->escapeString(response.getRaw());

    std::ostringstream oss;
    oss << "UPDATE transaction SET responseStatus = ";
    oss << response.getStatus().getCode();
    oss << ", contentType = \"" << response.getContentType() << "\", ";
    oss <<  "content = \"" << escapedContent << "\", ";
    oss << "verificationStatusId = 3, rawResponse = \"";
    oss << escapedRaw <<"\" WHERE id = " << tid;

    std::cout << oss.str() << std::endl;

    auto *stmt = con->createStatement();
    stmt->executeUpdate(oss.str());

    delete stmt;
  }

  HttpParserResult getServerResponse(const TransactionIdentifier & identifier) {
    std::ostringstream oss;
    oss << "SELECT responseStatus, contentType, content, rawResponse as raw FROM transaction ";
    oss << "WHERE id = " << identifier;

    auto *stmt = con -> createStatement();
    sql::ResultSet *res = stmt->executeQuery(oss.str());

    if (res->next()) {
      HttpParserResult ret(HttpParserResultState::RESPONSE);
      ret.setResponseStatus(HttpResponseStatus(res->getUInt("responseStatus")));
      ret.setContentType(res->getString("contentType"));
      ret.setContent(res->getString("content"));
      ret.setRaw(res->getString("raw"));

      delete stmt;
      delete res;
      return ret;
    } else {
      delete stmt;
      delete res;
      return HttpParserResult(HttpParserResultState::INVALID);
    }
  }

  bool isResponseAvailable(const TransactionIdentifier identifier) {
    std::ostringstream oss;
    oss << "SELECT COUNT(verificationStatusId) as count ";
    oss << "FROM transaction WHERE id = ";
    oss << identifier <<  " AND verificationStatusId >= 3";

    auto *stmt = con -> createStatement();
    sql::ResultSet *res = stmt->executeQuery(oss.str());

    bool available = false;
    if (res->next()) {
      available = (res->getUInt("count") > 0) ;
    }

    delete stmt;
    delete res;
    return available;
  }

  bool isRequestAvailable() {
    HelperRoutines::info("Is request available?");
    return getClientRequestCount() > 0;
  }

  void cleanup() {
    HelperRoutines::warning("Know what you do", "Deleting all transactions from database!");

    auto *stmt = con->createStatement();
    stmt->executeUpdate("DELETE FROM transaction");
    delete stmt;
  }

 private:
  const DatabaseConfiguration & config;
  sql::Driver *driver;
  sql::Connection *con;

  // prevent copy
  Database(const Database&) = delete;
  Database& operator=(const Database&) = delete;
};

#endif  // SRC_DB_DB_H_
