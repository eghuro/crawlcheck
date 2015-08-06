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
 public:
  virtual std::size_t getFindingId() const {
    return fid;
  }

  virtual std::size_t getResponseId() const {
    return rid;
  }

  virtual void setResponseId(std::size_t responseId) {
    rid = responseId;
  }

  explicit XMLFinding(std::size_t findingId):fid(findingId), rid(0) {}

  virtual ~XMLFinding() {}
 private:
  const std::size_t fid;
  std::size_t rid;
};

class XMLLink : public Link {
 public:
  virtual std::size_t getFindingId() const {
    return fid;
  }

  virtual HttpUri getUri() const {
    return uri;
  }
  virtual void setUri(const HttpUri & uri_) {
    uri = uri_;
  }

  virtual void setProcessed(bool processed_) {
    processed = processed_;
  }

  virtual bool getProcessed() const {
    return processed;
  }

  virtual void setRequestId(std::size_t rid_) {
    rid = rid_;
  }
  virtual std::size_t getRequestId() const {
    return rid;
  }

  explicit XMLLink(std::size_t findingId) : fid(findingId), uri(HttpUri()), processed(false), rid(0) {}
  virtual ~XMLLink() {}

 private:
  const std::size_t fid;
  HttpUri uri;
  bool processed;
  std::size_t rid;
};

class XMLDefect : public Defect {
 public:
  virtual std::size_t getFindingId() const {
    return fid;
  }

  virtual std::size_t getDefectType() const {
    return defect;
  }

  virtual void setDefectType(std::size_t type) {
    defect = type;
  }

  virtual void setEvidence(const std::string& evidence_) {
    evidence = evidence_;
  }

  virtual std::string getEvidence() const {
    return evidence;
  }

  virtual void setLocation(std::size_t location) {
    loc = location;
  }

  virtual std::size_t getLocation() const {
    return loc;
  }

  explicit XMLDefect(std::size_t findingId) : fid(findingId), evidence(), defect(0), loc(0) {}
  virtual ~XMLDefect();

 private:
  const std::size_t fid;
  std::string evidence;
  std::size_t defect, loc;
};

class XMLAnnotation : public Annotation {

};

class XMLDefectType : public DefectType {

};

class XMLVerificationStatus : public VerificationStatus {

};

class XMLConnector: public DatabaseConnector {
public:
  XMLConnector(const std::string & file) : fileName(file), transactionId(0), findingId(0) {}
  virtual ~XMLConnector() {}

  virtual Transaction * createTransaction() {
    std::shared_ptr<XMLTransaction> t = std::make_shared<XMLTransaction>(XMLTransaction(transactionId));
    transactions.insert( std::pair<std::size_t, std::shared_ptr<XMLTransaction> >(transactionId, t) );
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
  virtual Finding * createFinding() {
    std::shared_ptr<XMLFinding> f = std::make_shared<XMLFinding>(XMLFinding(findingId));
    findings.insert( std::pair<std::size_t, std::shared_ptr<XMLFinding> >(findingId, f));
    findingId++;
    return f.get();
  }
  virtual Finding * getFinding(std::size_t fid) const {
    auto it = findings.find(fid);
    if (it != findings.end()) {
      return std::get<1>((*it)).get();
    } else {
      return nullptr;
    }
  }
  virtual Link * createLink(Finding * finding) {
    std::shared_ptr<XMLLink> l = std::make_shared<XMLLink>(XMLLink(finding->getFindingId()));
    links.insert( std::pair<std::size_t, std::shared_ptr<XMLLink>>(finding->getFindingId(), l));
    return l.get();
  }
  virtual Link * getLink(std::size_t fid) const {
    auto it = links.find(fid);
    if (it != links.end()) {
      return std::get<1>((*it)).get();
    } else {
      return nullptr;
    }
  }

  virtual Defect * createDefect(Finding * finding) {
    auto d = std::make_shared<XMLDefect>(XMLDefect(finding->getFindingId()));
    defects.insert(std::pair<std::size_t, std::shared_ptr<XMLDefect>>(finding->getFindingId(), d));
    return d.get();
  }
  virtual Defect * getDefect(std::size_t fid) const {
    auto it = defects.find(fid);
    if (it != defects.end()) {
      return std::get<1>((*it)).get();
    } else {
      return nullptr;
    }
  }
  virtual Annotation * createAnnotation() { return nullptr; }
  virtual Annotation * getAnnotation(std::size_t) const { return nullptr; }
  virtual DefectType * createDefectType() { return nullptr; }
  virtual DefectType * getDefectType(std::size_t) const { return nullptr; }
  virtual VerificationStatus * createVerificationStatus() { return nullptr; }
  virtual VerificationStatus * getVerificationStatus(std::size_t) const { return nullptr; }

 private:
  std::size_t transactionId, findingId;
  std::map<std::size_t, std::shared_ptr<XMLTransaction>> transactions;
  std::map<std::size_t, std::shared_ptr<XMLFinding>> findings;
  std::map<std::size_t, std::shared_ptr<XMLLink>> links;
  std::map<std::size_t, std::shared_ptr<XMLDefect>> defects;

  const std::string fileName;
};

#endif  // SRC_DB_XMLCONNECTOR_H_
