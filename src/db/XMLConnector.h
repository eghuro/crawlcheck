// Copyright 2015 alex
#ifndef SRC_DB_XMLCONNECTOR_H_
#define SRC_DB_XMLCONNECTOR_H_

#include <memory>
#include <map>
#include <cassert>
#include <iostream>
#include <xercesc/dom/DOM.hpp>
#include <xercesc/dom/DOMDocument.hpp>
#include <xercesc/dom/DOMDocumentType.hpp>
#include <xercesc/dom/DOMElement.hpp>
#include <xercesc/dom/DOMImplementation.hpp>
#include <xercesc/dom/DOMImplementationLS.hpp>
#include <xercesc/dom/DOMNodeIterator.hpp>
#include <xercesc/dom/DOMNodeList.hpp>
#include <xercesc/dom/DOMText.hpp>
#include <xercesc/parsers/XercesDOMParser.hpp>
#include <xercesc/util/XMLUni.hpp>
#include <xercesc/sax/HandlerBase.hpp>
#include <xercesc/util/XMLString.hpp>
#include <xercesc/util/PlatformUtils.hpp>
#include <xercesc/framework/LocalFileFormatTarget.hpp>
#include <sys/stat.h>


#include "TableInterfaces.h"

using namespace xercesc;

class XMLUtils {
 public:
  static int serializeDOM(DOMNode* node, const std::string & name) {
    std::cout << "Serialize" <<std::endl;
    std::cout << name << std::endl;
    /*XMLCh tempStr[100];
    XMLString::transcode("LS", tempStr, 99);
    DOMImplementation *impl = DOMImplementationRegistry::getDOMImplementation(tempStr);
    DOMLSSerializer* theSerializer = ((DOMImplementationLS*)impl)->createLSSerializer();

    // optionally you can set some features on this serializer
    /*if (theSerializer->getDomConfig()->canSetParameter(XMLUni::fgDOMWRTDiscardDefaultContent, true))
        theSerializer->getDomConfig()->setParameter(XMLUni::fgDOMWRTDiscardDefaultContent, true);

    if (theSerializer->getDomConfig()->canSetParameter(XMLUni::fgDOMWRTFormatPrettyPrint, true))
         theSerializer->getDomConfig()->setParameter(XMLUni::fgDOMWRTFormatPrettyPrint, true);*/

    // StdOutFormatTarget prints the resultant XML stream
    // to stdout once it receives any thing from the serializer.
    /*std::cout << "Get array" <<std::endl;
    XMLCh * fname = new XMLCh[name.length()+1];
    std::cout << "transcode" << std::endl;
    XMLString::transcode(name.c_str(), fname, name.length());

    XMLFormatTarget *myFormTarget = new LocalFileFormatTarget(fname);
    DOMLSOutput* theOutput = ((DOMImplementationLS*)impl)->createLSOutput();
    theOutput->setByteStream(myFormTarget);

    try {
        // do the serialization through DOMLSSerializer::write();
        theSerializer->write(node, theOutput);
    }
    catch (const XMLException& toCatch) {
        char* message = XMLString::transcode(toCatch.getMessage());
        std::cout << "Exception message is: \n"
             << message << "\n";
        XMLString::release(&message);
        return -1;
    }
    catch (const DOMException& toCatch) {
        char* message = XMLString::transcode(toCatch.msg);
        std::cout << "Exception message is: \n"
             << message << "\n";
        XMLString::release(&message);
        return -1;
    }
    catch (...) {
        std::cout << "Unexpected Exception \n" ;
        return -1;
    }

    std::cout << "Releasing resources" << std::endl;
    theOutput->release();
    theSerializer->release();
    delete fname;
    delete myFormTarget;*/
    return 0;
  }
};

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

  explicit XMLTransaction(std::size_t id_, DOMDocument * doc): id(id_), document(doc), responseStatus(0),
    method(RequestMethod::GET) {}
  virtual ~XMLTransaction() {
    /*DOMElement *root = document->getDocumentElement();

    XMLCh tempStr[100];
    XMLString::transcode("Transaction", tempStr, 99);
    DOMElement *e = document->createElement(tempStr);
    root->appendChild(e);*/
  }

 private:
  const std::size_t id;
  std::size_t verificationStatus;
  std::shared_ptr<std::string> content;
  std::string contentType;
  HttpResponseStatus responseStatus;
  HttpUri uri;
  RequestMethod method;

  DOMDocument * document;
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
  virtual ~XMLDefect() {}

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
  XMLConnector(const std::string & file) : fileName(file), transactionId(0), findingId(0) {
    document = nullptr;
    initialize(file.c_str(), &document);
    std::cout << "Initialized" << std::endl;
    assert(document != nullptr);
  }
  virtual ~XMLConnector() {
    std::cout << "Destructor" << std::endl;
    std::cout << "True "  << true << std::endl;
    std::cout << (document != NULL) << std::endl;
    std::cout << fileName << std::endl;
    saveData();
    std::cout << "Destructed" << std::endl;
  }

  void saveData() {
    auto el = document->getDocumentElement();
    XMLUtils::serializeDOM(el, fileName);
  }

  virtual Transaction * createTransaction() {
    std::shared_ptr<XMLTransaction> t = std::make_shared<XMLTransaction>(XMLTransaction(transactionId, document));
    transactions.insert( std::pair<std::size_t, std::shared_ptr<XMLTransaction> >(transactionId, t) );
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

  DOMDocument * document;

  inline bool exists (const std::string& name) {
    struct stat buffer;
    return (stat (name.c_str(), &buffer) == 0);
  }

  bool initialize(const char * xmlFileName, DOMDocument ** outDocument) {
    try {
      XMLPlatformUtils::Initialize();
    }
    catch (const XMLException & toCatch) {
      char * message = XMLString::transcode(toCatch.getMessage());
      std::cout << "Error during XML initialization : " << message << std::endl;
      XMLString::release(&message);
      return false;
    }

    XercesDOMParser* parser = new XercesDOMParser();
    parser->setValidationScheme(XercesDOMParser::Val_Always);

    ErrorHandler* errHandler = (ErrorHandler*) new HandlerBase();
    parser->setErrorHandler(errHandler);

    *outDocument = nullptr;

    if (exists(xmlFileName)) {
      std::cout<<"Exists"<<std::endl;
      try {
        std::cout<<"Parsing"<<std::endl;
        parser->parse(xmlFileName);
        std::cout<<"Parsed"<<std::endl;
      }
      catch (const XMLException & toCatch) {
        char * message = XMLString::transcode(toCatch.getMessage());
        std::cout << "XML Exception: " << message << std::endl;
        XMLString::release(&message);
        return false;
      }
      catch (const DOMException & toCatch) {
        char * message = XMLString::transcode(toCatch.getMessage());
        std::cout << "DOM Exception: " << message << std::endl;
        XMLString::release(&message);
        return false;
      }
      catch (...) {
        std::cout << "Unexpected exception" << std::endl;
        return false;
      }

      std::cout << "Get document" << std::endl;
      *outDocument = parser->getDocument();
      std::cout << "Got it" << std::endl;
    } else {
      XMLCh tempStr[100];

      XMLString::transcode("Range", tempStr, 99);
      DOMImplementation* impl = DOMImplementationRegistry::getDOMImplementation(tempStr);

      XMLString::transcode("crawldb", tempStr, 99);
      *outDocument = impl->createDocument(0, tempStr, 0);
    }

    assert (outDocument != nullptr);

    delete parser;
    delete errHandler;
    return true;
  }
};

#endif  // SRC_DB_XMLCONNECTOR_H_
