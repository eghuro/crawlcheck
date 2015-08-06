// Copyright 2015 alex
#ifndef SRC_DB_XMLCONNECTOR_H_
#define SRC_DB_XMLCONNECTOR_H_

#include <memory>
#include <map>
#include "TableInterfaces.h"

class XMLTransaction : public Transaction {
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

  explicit XMLTransaction(std::size_t id_): id(id_), responseStatus(0), method(RequestMethod::GET) {}
  virtual ~XMLTransaction() {}

 private:
  const std::size_t id;
  std::size_t verificationStatus;
  std::shared_ptr<std::string> content;
  std::string contentType;
  HttpResponseStatus responseStatus;
  HttpUri uri;
  RequestMethod method;
};

class XMLFinding : public Finding {

};

class XMLLink : public Link {

};

class XMLDefect : public Defect {

};

class XMLAnnotation : public Annotation {

};

class XMLDefectType : public DefectType {

};

class XMLVerificationStatus : public VerificationStatus {

};

class XMLConnector: public DatabaseConnector {
public:
  XMLConnector(const std::string & file) : fileName(file), transactionId(0) {}
  virtual ~XMLConnector() {}

  virtual Transaction * createTransaction() {
    std::shared_ptr<XMLTransaction> t = std::make_shared<XMLTransaction>(XMLTransaction(transactionId));
    //transactions.insert( std::pair<std::size_t, int>(transactionId, 0) );
    transactionId++;
    return t.get();
  }
  virtual Transaction * getTransaction(std::size_t tid) const {
    auto it = transactions.find(tid);
    if (it != transactions.end()) {
      return std::get<1>((*it)).get();
    } else {
      return nullptr;
    }
  }
  virtual Finding * createFinding() const { return nullptr; }
  virtual Finding * getFinding(std::size_t) const { return nullptr; }
  virtual Link * createLink(Finding * finding) const { return nullptr; }
  virtual Link * getLink(std::size_t) const { return nullptr; }
  virtual Defect * createDefect(Finding *) const { return nullptr; }
  virtual Defect * getDefect(std::size_t) const { return nullptr; }
  virtual Annotation * createAnnotation() const { return nullptr; }
  virtual Annotation * getAnnotation(std::size_t) const { return nullptr; }
  virtual DefectType * createDefectType() const { return nullptr; }
  virtual DefectType * getDefectType(std::size_t) const { return nullptr; }
  virtual VerificationStatus * createVerificationStatus() const { return nullptr; }
  virtual VerificationStatus * getVerificationStatus(std::size_t) const { return nullptr; }
 private:
  std::size_t transactionId;
  typedef std::pair<std::size_t, std::shared_ptr<XMLTransaction>> map_t;
  std::map<std::size_t, std::shared_ptr<XMLTransaction>> transactions;//

  const std::string fileName;
};

#endif  // SRC_DB_XMLCONNECTOR_H_
