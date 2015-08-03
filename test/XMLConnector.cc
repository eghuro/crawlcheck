// Copyright 2015 Alexandr Mansurov

#include <memory>
#include "../src/db/TableInterfaces.h"
TEST(XmlConnector, Create) {
  std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
}

TEST(XmlConnector, Transaction) {
  std::shared_ptr<DatabaseConnector> c = std::make_shared<DatabaseConnector>(XMLConnector("/tmp/ccdb.xml"));
  auto tr = c->createTransaction();

  ASSERT_EQ(tr->getId(), 0);

  tr->setMethod(RequestMethod::GET);
  ASSERT_EQ(tr->getMethod(), RequestMethod::GET);

  tr->setMethod(RequestMethod::POST);
  ASSERT_EQ(tr->getMethod(), RequestMethod::POST);

  tr->setMethod(RequestMethod::PUT);
  ASSERT_EQ(tr->getMethod(), RequestMethod::PUT);

  tr->setMethod(RequestMethod::HEAD);
  ASSERT_EQ(tr->getMethod(), RequestMethod::HEAD);

  tr->setMethod(RequestMethod::CONNECT);
  ASSERT_EQ(tr->getMethod(), RequestMethod::CONNECT);

  // TODO(alex): nasetit, getnout transakci dle ID, asserty
}



