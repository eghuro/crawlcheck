// Copyright 2015 Alexandr Mansurov

#include <memory>
#include "../src/db/TableInterfaces.h"
#include "../src/db/XMLConnector.h"
#include "gtest/gtest.h"

TEST(XmlConnector, Create) {
  //const std::shared_ptr<DatabaseConnector> c = std::make_shared<XMLConnector>(XMLConnector("/tmp/ccdb.xml"));
  const DatabaseConnector * c = new XMLConnector("/tmp/ccdb.xml");
  delete c;
}

TEST(XmlConnectorTransaction, RequestMethodGet) {
  //const std::shared_ptr<DatabaseConnector> c = std::make_shared<XMLConnector>(XMLConnector("/tmp/ccdb.xml"));
  DatabaseConnector * c = new XMLConnector("/tmp/ccdb.xml");

  auto tr(c -> createTransaction());

  ASSERT_TRUE(0 == tr->getId());

  tr->setMethod(RequestMethod::GET);
  ASSERT_TRUE(tr->getMethod() == RequestMethod::GET);

  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<XMLConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr2(c2->getTransaction(0));

  ASSERT_FALSE(tr2 == nullptr);
  ASSERT_TRUE(0 == tr2->getId());
  ASSERT_TRUE(tr2->getMethod() == RequestMethod::GET);
}

/*TEST(XmlConnectorTransaction, RequestMethodPost) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));

  auto tr(c -> createTransaction());

  ASSERT_TRUE(1 == tr->getId());

  tr->setMethod(RequestMethod::POST);
  ASSERT_TRUE(tr->getMethod() == RequestMethod::POST);

  delete c;
  ASSERT_EQ(nullptr, c);

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr2(c2->getTransaction(1));

  ASSERT_TRUE(1 == tr2->getId());
  ASSERT_TRUE(tr2->getMethod() == RequestMethod::POST);
}

TEST(XmlConnectorTransaction, RequestMethodConnect) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));

  auto tr(c -> createTransaction());

  ASSERT_TRUE(2 == tr->getId());

  tr->setMethod(RequestMethod::CONNECT);
  ASSERT_TRUE(tr->getMethod() == RequestMethod::CONNECT);

  delete c;
  ASSERT_EQ(nullptr, c);

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr2(c2->getTransaction(2));

  ASSERT_TRUE(2 == tr2->getId());
  ASSERT_TRUE(tr2->getMethod() == RequestMethod::CONNECT);
}

TEST(XmlConnectorTransaction, RequestMethodPut) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));

  auto tr(c -> createTransaction());

  ASSERT_TRUE(3 == tr->getId());

  tr->setMethod(RequestMethod::PUT);
  ASSERT_TRUE(tr->getMethod() == RequestMethod::PUT);

  delete c;
  ASSERT_EQ(nullptr, c);

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr2(c2->getTransaction(3));

  ASSERT_TRUE(3 == tr2->getId());
  ASSERT_TRUE(tr2->getMethod() == RequestMethod::PUT);
}

TEST(XmlConnectorTransaction, RequestMethodHead) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));

  auto tr(c -> createTransaction());

  ASSERT_TRUE(4 == tr->getId());

  tr->setMethod(RequestMethod::HEAD);
  ASSERT_TRUE(tr->getMethod() == RequestMethod::HEAD);

  delete c;
  ASSERT_EQ(nullptr, c);

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr2(c2->getTransaction(4));

  ASSERT_TRUE(4 == tr2->getId());
  ASSERT_TRUE(tr2->getMethod() == RequestMethod::HEAD);
}

TEST(XmlConnectorTransaction, Values) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));

  auto tr(c -> createTransaction());

  auto id(tr->getId());

  const HttpUri uri(HttpUriFactory::createUri("http://olga.majling.eu/Vyuka"))
  const ResponseStatus status(200);
  const std::string ctype("text/html");
  const std::string content("<html></html>");
  const std::size_t verificationStatus(3);

  tr->setUri(uri);
  ASSERT_EQ(uri, tr->getUri());

  tr->setResponseStatus(status);
  ASSERT_EQ(status, tr->getResponseStatus());

  tr->setContentType(ctype);
  ASSERT_EQ(ctype, tr->getContentType());

  tr->setContent(content);
  ASSERT_EQ(content, tr->getContent());

  tr->setContent("");
  ASSERT_EQ("", tr->getContent());

  tr->setContent(&content);
  ASSERT_EQ(content, *(tr->getContent()));

  tr->setVerificationStatus(verificationStatus);
  ASSERT_EQ(verificationStatus, tr->getVerificationStatus());

  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr2(c2->getTransaction(id));
  ASSERT_EQ(id, tr2->getId());
  ASSERT_EQ(uri, tr2->getUri())
  ASSERT_EQ(ctype, tr2->getContentType());
  ASSERT_EQ(content, tr2->getContent());
  ASSERT_EQ(content, *(tr->getContent()));
  ASSERT_EQ(verificationStatus, tr2->getVerificationStatus());
}

//TODO 2 DB independent

TEST(XmlConnector, Finding) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));

  auto tr(c -> createTransaction());

  auto f(c -> createFinding());
  ASSERT_EQ(0, f->getFindingId());

  auto id tr->getId());
  f->setResponseId(id);
  ASSERT_EQ(id, f->getResponseId())

  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto f2(c2->getFinding(0));

  ASSERT_EQ(0, f2->getFindingId());
  ASSERT_EQ(id, f2->getResponseId());
}

TEST(XmlConnector, Link) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr -> createTransaction());
  auto f -> createFinding());

  auto link(c->createLink(f));
  ASSERT_EQ(f->getFindingId(), link->getFindingId());

  auto uri(HttpUriFactory::createUri("http://www.cvut.cz"));
  link->setUri(uri);
  ASSERT_EQ(uri, link->getUri());

  ASSERT_FALSE(link->getProcessed());
  link->setProcessed(true);
  ASSERT_TRUE(link->getProcessed());

  auto id(tr->getId());
  link->setRequestId(id);
  ASSERT_EQ(id, link->getRequestId());

  auto fid(f->getFindingId());
  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto l(c2->getLink(fid));
  ASSERT_EQ(l->getFindingId(), fid);
  ASSERT_EQ(l->getUri(), uri);
  ASSERT_TRUE(l->getProcessed());
  ASSERT_EQ(id, l->getRequestId());
}

TEST(XmlConnector, Defect) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr(c -> createTransaction());
  auto f(c -> createFinding());

  auto id = d->getFindingId();

  auto d(c->createDefect(f));

  ASSERT_EQ(f->getFindingId(), id);

  const std::size_t type(8);
  const std::string evidence("...");
  const std::size_t location(7);

  d->setDefectType(type);
  d->setEvidence(evidence);
  d->setLocation(location);

  ASSERT_EQ(type, d->getDefectType());
  ASSERT_EQ(evidence, d->getEvidence());
  ASSERT_EQ(locatiom, d->getLocation());

  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto d2(c2->getDefect(id));

  ASSERT_EQ(id, d2->getFindingId());
  ASSERT_EQ(type, d2->getDefectType());
  ASSERT_EQ(evidence, d2->getEvidence());
  ASSERT_EQ(locatiom, d2->getLocation());
}

TEST(XmlConnector, Annotation) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr(c -> createTransaction());
  auto f(c -> createFinding());
  auto an(c->createAnnotation(f));

  auto id(f->getFindingId);;
  ASSERT_EQ(id, an->getFindingId());

  const std::string comment("Comment");
  an->setComment(comment);
  ASSERT_EQ(comment, an->getComment());

  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto an2(c2->getAnnotation(id));
  ASSERT_EQ(id, an->getFindingId());
  ASSERT_EQ(comment, an->getComment());
}

TEST(XmlConnector, DefectType) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto d(c->createDefectType());

  ASSERT_EQ(0, d->getId());

  const std::string desc("...");
  d->setDescription(desc);

  ASSERT_EQ(desc, d->getDescription());

  delete c;
  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto d2(c2->getDefectType(0));
  ASSERT_EQ(0, d2->getId());
  ASSERT_EQ(desc, d2->getDescription());
}

TEST(XmlConnector, VerificationStatus) {
  const std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto vs(c->createVerificationStatus());

  ASSERT_EQ(0, vs->getId());

  const std::string desc("...");
  vs->setDescription(desc);
  ASSERT_EQ(desc, vs->getDescription());

  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto vs2(c2->getVerificationStatus(0));

  ASSERT_EQ(0, vs2->getId());
  ASSERT_EQ(desc, vs2->getDescription());
}*/
