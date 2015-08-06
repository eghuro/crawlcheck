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

 protected:
  // explicit virtual VerificationStatus(std::size_t id);
  virtual ~VerificationStatus();

 private:
  VerificationStatus() = delete;
};

class Transaction {


};

class Finding {
 public:
  virtual std::size_t getFindingId() const;
  virtual std::size_t getResponseId() const;
  virtual void setResponseId(std::size_t responseId);

 protected:
  // explicit virtual Finding(std::size_t findingId);
  virtual ~Finding();

 private:
   Finding() = delete;
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

 protected:
  // explicit virtual Link(std::size_t findingId);
  virtual ~Link();

 private:
  Link() = delete;
};

class DefectType {
 public:
  virtual std::size_t getId() const;
  virtual void setDescription(const std::string &) const;
  virtual std::string getDescription();

 protected:
  // explicit virtual DefectType(std::size_t id);
  virtual ~DefectType();

 private:
  DefectType() = delete;
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

 protected:
  // explicit virtual Defect(std::size_t findingId);
  virtual ~Defect();

 private:
  Defect() = delete;
};

class Annotation {
 public:
  virtual std::size_t getFindingId() const;
  virtual std::string getComment() const;
  virtual void setComment(const std::string &);

 protected:
  // explicit Annotation(std::size_t findingId);
  virtual ~Annotation();

 private:
  Annotation() = delete;
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
