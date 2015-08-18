// Copyright 2015 Alexandr Mansurov

#include <memory>
#include "../src/proxy/db.h"
#include "../src/proxy/ProxyConfiguration.h"
#include "../src/proxy/RequestStorage.h"
#include "../src/proxy/ServerAgent.h"
#include "../src/proxy/ClientAgent.h"
#include "gtest/gtest.h"

/*TEST(Main, Creation) {
  ProxyConfiguration pc;

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  std::shared_ptr<RequestStorage> rs(new RequestStorage(db));
}

TEST(ServerAgent, CreateServerAgent) {
  ProxyConfiguration pc;
  pc.setOutPoolCount(2);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  std::shared_ptr<RequestStorage> rs(new RequestStorage(db));

  ServerAgent sa(pconf, rs);
}

TEST(ServerAgent, CreateServerAgentNoThreads) {
  ProxyConfiguration pc;
  pc.setOutPoolCount(0);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  std::shared_ptr<RequestStorage> rs(new RequestStorage(db));

  ServerAgent sa(pconf, rs);
}

TEST(ServerAgent, CreateServerAgentNegativeThreads) {
  ProxyConfiguration pc;
  ASSERT_FALSE(pc.setOutPoolCount(-2));
  ASSERT_EQ(0, pc.getOutPoolCount());

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  std::shared_ptr<RequestStorage> rs(new RequestStorage(db));

  ServerAgent sa(pconf, rs);
}*/

TEST(ServerAgent, Start) {
  ProxyConfiguration pc;
  pc.setOutPoolCount(1);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  std::shared_ptr<RequestStorage> rs(new RequestStorage(db));

  ServerAgent sa(pconf, rs);
  sa.start();
}

/*TEST(ClientAgent, CreateClientAgent) {
  ProxyConfiguration pc;

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  std::shared_ptr<RequestStorage> rs(new RequestStorage(db));

  ClientAgent client(pconf, rs);
}*/
