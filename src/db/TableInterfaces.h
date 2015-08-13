// Copyright 2015 Alexandr Mansurov
#ifndef SRC_DB_TABLEINTERFACES_H_
#define SRC_DB_TABLEINTERFACES_H_

#include "../proxy/HttpParser.h"

enum RequestMethod {
  GET, POST, PUT, CONNECT, HEAD
};

class VerificationStatus {
 public:
  virtual std::size_t getId() const;

  virtual std::string getDescription() const;
  virtual void setDescription(const std::string & description);
};

class Transaction {
 public:
  virtual std::size_t getId() const = 0;

  virtual void setMethod(const RequestMethod & method) = 0;
  virtual RequestMethod getMethod() const = 0;

  virtual void setUri(const HttpUri & uri) = 0;
  virtual HttpUri getUri() const = 0;

  virtual void setResponseStatus(const HttpResponseStatus & status) = 0;
  virtual HttpResponseStatus getResponseStatus() const = 0;

  virtual void setContentType(const std::string & ctype) = 0;
  virtual std::string getContentType() const = 0;

  virtual void setContent(const std::string & content) = 0;
  virtual void setContent(std::string * content) = 0;

  virtual std::string getContent() const = 0;
  virtual std::string * getContent() = 0;

  virtual void setVerificationStatus(std::size_t id) = 0;
  virtual std::size_t getVerificationStatus() const = 0;
};

class Finding {
 public:
  virtual std::size_t getFindingId() const = 0;
  virtual std::size_t getResponseId() const = 0;
  virtual void setResponseId(std::size_t responseId) = 0;
};

class Link {
 public:
  virtual std::size_t getFindingId() const = 0;

  virtual HttpUri getUri() const = 0;
  virtual void setUri(const HttpUri & uri) = 0;

  virtual void setProcessed(bool) = 0;
  virtual bool getProcessed() const = 0;

  virtual void setRequestId(std::size_t) = 0;
  virtual std::size_t getRequestId() const = 0;
};

class DefectType {
 public:
  virtual std::size_t getId() const = 0;
  virtual void setDescription(const std::string &) const = 0;
  virtual std::string getDescription() = 0;
};

class Defect {
 public:
  virtual std::size_t getFindingId() const = 0;

  virtual std::size_t getDefectType() const = 0;
  virtual void setDefectType(std::size_t) = 0;

  virtual void setEvidence(const std::string& evidence) = 0;
  virtual std::string getEvidence() const = 0;

  virtual void setLocation(std::size_t) = 0;
  virtual std::size_t getLocation() const = 0;
};

class Annotation {
 public:
  virtual std::size_t getFindingId() const = 0;
  virtual std::string getComment() const = 0;
  virtual void setComment(const std::string &) = 0;
};

class DatabaseConnector {
 public:
  virtual Transaction * createTransaction(const RequestMethod, const HttpUri &) = 0;
  virtual Transaction * getTransaction(std::size_t) const = 0;
  virtual Finding * createFinding(std::size_t) = 0;
  virtual Finding * getFinding(std::size_t) const = 0;
  virtual Link * createLink(Finding * finding, const HttpUri &) = 0;
  virtual Link * getLink(std::size_t) const = 0;
  virtual Defect * createDefect(Finding *) = 0;
  virtual Defect * getDefect(std::size_t) const = 0;
  virtual Annotation * createAnnotation() = 0;
  virtual Annotation * getAnnotation(std::size_t) const = 0;
  virtual DefectType * createDefectType() = 0;
  virtual DefectType * getDefectType(std::size_t) const = 0;
  virtual VerificationStatus * createVerificationStatus() = 0;
  virtual VerificationStatus * getVerificationStatus(std::size_t) const = 0;
  virtual ~DatabaseConnector() {}
};
#endif  // SRC_DB_TABLEINTERFACES_H_
