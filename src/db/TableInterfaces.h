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
  virtual std::size_t getId() const;

  virtual void setMethod(const RequestMethod & method);
  virtual RequestMethod getMethod() const;

  virtual void setUri(const HttpUri & uri);
  virtual HttpUri getUri() const;

  virtual void setResponseStatus(const HttpResponseStatus & status);
  virtual HttpResponseStatus getResponseStatus() const;

  virtual void setContentType(const std::string & ctype);
  virtual std::string getContentType() const;

  virtual void setContent(const std::string & content);
  virtual void setContent(std::string * content);

  virtual std::string getContent() const;
  virtual std::string * getContent();

  virtual void setVerificationStatus(std::size_t id);
  virtual std::size_t getVerificationStatus() const;
};

class Finding {
 public:
  virtual std::size_t getFindingId() const;
  virtual std::size_t getResponseId() const;
  virtual void setResponseId(std::size_t responseId);
};

class Link {
 public:
  virtual std::size_t getFindingId() const;

  virtual HttpUri getUri() const;
  virtual void setUri(const HttpUri & uri);

  virtual void setProcessed(bool);
  virtual bool getProcessed() const;

  virtual void setRequestId(std::size_t);
  virtual std::size_t getRequestId() const;
};

class DefectType {
 public:
  virtual std::size_t getId() const;
  virtual void setDescription(const std::string &) const;
  virtual std::string getDescription();
};

class Defect {
 public:
  virtual std::size_t getFindingId() const;

  virtual std::size_t getDefectType() const;
  virtual void setDefectType(std::size_t);

  virtual void setEvidence(const std::string& evidence);
  virtual std::string getEvidence() const;

  virtual void setLocation(std::size_t);
  virtual std::size_t getLocation() const;
};

class Annotation {
 public:
  virtual std::size_t getFindingId() const;
  virtual std::string getComment() const;
  virtual void setComment(const std::string &);
};

class DatabaseConnector {
 public:
  virtual Transaction * createTransaction();
  virtual Transaction * getTransaction(std::size_t) const;
  virtual Finding * createFinding();
  virtual Finding * getFinding(std::size_t) const;
  virtual Link * createLink(Finding * finding);
  virtual Link * getLink(std::size_t) const;
  virtual Defect * createDefect(Finding *);
  virtual Defect * getDefect(std::size_t) const;
  virtual Annotation * createAnnotation();
  virtual Annotation * getAnnotation(std::size_t) const;
  virtual DefectType * createDefectType();
  virtual DefectType * getDefectType(std::size_t) const;
  virtual VerificationStatus * createVerificationStatus();
  virtual VerificationStatus * getVerificationStatus(std::size_t) const;
  virtual ~DatabaseConnector();
};
#endif  // SRC_DB_TABLEINTERFACES_H_
