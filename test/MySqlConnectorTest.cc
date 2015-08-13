// Copyright 2015 Alexandr Mansurov

#include <memory>
#include "../src/db/TableInterfaces.h"
#include "../src/db/MySqlConnector.h"
#include "gtest/gtest.h"

TEST(MySqlConnector, Create) {
  //const std::shared_ptr<DatabaseConnector> c = std::make_shared<XMLConnector>(XMLConnector("/tmp/ccdb.xml"));
  const DatabaseConnector * c = new MySqlConnector("localhost", "test", "", "Crawlcheck");
  delete c;
}

TEST(MySqlConnectorTransaction, RequestMethodGet) {
  //const std::shared_ptr<DatabaseConnector> c = std::make_shared<XMLConnector>(XMLConnector("/tmp/ccdb.xml"));
  DatabaseConnector * c = new MySqlConnector("localhost", "test", "", "Crawlcheck");

  auto tr(c -> createTransaction());

  ASSERT_TRUE(0 == tr->getId());

  tr->setMethod(RequestMethod::GET);
  ASSERT_TRUE(tr->getMethod() == RequestMethod::GET);

  delete c;

  const std::shared_ptr<DatabaseConnector> c2 = std::make_shared<MySqlConnector>(MySqlConnector("localhost", "test", "", "Chrawlcheck"));
  auto tr2(c2->getTransaction(0));

  ASSERT_FALSE(tr2 == nullptr);
  ASSERT_TRUE(0 == tr2->getId());
  ASSERT_TRUE(tr2->getMethod() == RequestMethod::GET);
}
