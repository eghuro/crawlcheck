// Copyright 2015 Alexandr Mansurov
#ifndef SRC_DB_MYSQLCONNECTOR_H_
#define SRC_DB_MYSQLCONNECTOR_H_

#include <map>
#include <memory>
#include "mysql_driver.h"
#include "TableInterfaces.h"

class MySqlTransaction : public Transaction {
public:
  virtual std::size_t getId() const {
    return id;
  }

  virtual void setMethod(const RequestMethod & method_) {
    method = method_;
  }

  virtual RequestMethod getMethod() const {
    return method;
  }

  virtual void setUri(const HttpUri & uri_) {
    uri = uri_;
  }

  virtual HttpUri getUri() const {
    return uri;
  }

  virtual void setResponseStatus(const HttpResponseStatus & status) {
    responseStatus = status;
  }

  virtual HttpResponseStatus getResponseStatus() const {
    return responseStatus;
  }

  virtual void setContentType(const std::string & ctype) {
    contentType = ctype;
  }

  virtual std::string getContentType() const {
    return contentType;
  }

  virtual void setContent(const std::string & content_) {
    content = std::make_shared<std::string>(content_);
  }

  virtual void setContent(std::string * content_) {
    content = std::shared_ptr<std::string>(content_);
  }

  virtual std::string getContent() const {
    return *content;
  }

  virtual std::string * getContent() {
    return content.get();
  }

  virtual void setVerificationStatus(std::size_t id) {
    verificationStatus = id;
  }
  virtual std::size_t getVerificationStatus() const {
    return verificationStatus;
  }

  explicit MySqlTransaction(std::size_t id_): id(id_), responseStatus(0),
      method(RequestMethod::GET) {}

private:
  const std::size_t id;
  std::size_t verificationStatus;
  std::shared_ptr<std::string> content;
  std::string contentType;
  HttpResponseStatus responseStatus;
  HttpUri uri;
  RequestMethod method;
};

class MySqlConnector: public DatabaseConnector {
public:
  MySqlConnector(const std::string & srvr, const std::string & usr, const std::string & pwd, const std::string & db):
    server(srvr), user(usr), password(pwd), database(db), transactionId(0) {
    driver = get_driver_instance();
    con = driver->connect(server, user, password);
  }
  virtual ~MySqlConnector() {
    delete con;
  }

  virtual Transaction * createTransaction() {
    std::shared_ptr<MySqlTransaction> t = std::make_shared<MySqlTransaction>(MySqlTransaction(transactionId));
    transactions.insert( std::pair<std::size_t, std::shared_ptr<MySqlTransaction> >(transactionId, t) );
    if (transactions.find(0) == transactions.end()) {
      assert(false);
    }
    transactionId++;
    return t.get();
  }

  virtual Transaction * getTransaction(std::size_t tid) const {
    std::cout << "Get transaction "<<tid<<std::endl;
    auto it = transactions.find(tid);
    if (it != transactions.end()) {
      std::cout <<"Found"<<std::endl;
      return std::get<1>((*it)).get();
    } else {
      return nullptr;
    }
  }

  virtual Finding * createFinding() {
    return nullptr;
  }

  virtual Finding * getFinding(std::size_t) const {
    return nullptr;
  }

  virtual Link * createLink(Finding * finding) {
    return nullptr;
  }

  virtual Link * getLink(std::size_t) const {
    return nullptr;
  }

  virtual Defect * createDefect(Finding *) {
    return nullptr;
  }

  virtual Defect * getDefect(std::size_t) const {
    return nullptr;
  }

  virtual Annotation * createAnnotation() {
    return nullptr;
  }

  virtual Annotation * getAnnotation(std::size_t) const {
    return nullptr;
  }

  virtual DefectType * createDefectType() {
    return nullptr;
  }

  virtual DefectType * getDefectType(std::size_t) const {
    return nullptr;
  }

  virtual VerificationStatus * createVerificationStatus() {
    return nullptr;
  }

  virtual VerificationStatus * getVerificationStatus(std::size_t) const {
    return nullptr;
  }
private:
  const std::string server, user, password, database;

  std::size_t transactionId;
  std::map<std::size_t, std::shared_ptr<MySqlTransaction>> transactions;

  sql::Driver *driver;
  sql::Connection *con;
};

#endif  // SRC_DB_MYSQLCONNECTOR_H_
