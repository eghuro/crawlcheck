// Copyright 2015 Alexandr Mansurov

#include <memory>
#include "../src/proxy/db.h"
#include "../src/proxy/ProxyConfiguration.h"
#include "../src/proxy/RequestStorage.h"
#include "../src/proxy/ServerAgent.h"
#include "../src/proxy/ClientAgent.h"
#include "gtest/gtest.h"
#include "./exhibit.h"

TEST(Exhibit, exhibit) {
  a mya;
  mya.start();
}

TEST(Main, Creation) {
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
  RequestStorage * rs = new RequestStorage(db);
  pthread_mutex_t rslock(PTHREAD_MUTEX_INITIALIZER);

  ServerAgent sa(pconf, rs, &rslock);

  delete rs;
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
  RequestStorage * rs = new RequestStorage(db);
  pthread_mutex_t rslock(PTHREAD_MUTEX_INITIALIZER);

  ServerAgent sa(pconf, rs, &rslock);

  delete rs;
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
  RequestStorage * rs = new RequestStorage(db);
  pthread_mutex_t rslock(PTHREAD_MUTEX_INITIALIZER);

  ServerAgent sa(pconf, rs, &rslock);

  delete rs;
}

TEST(ClientWorkerParameters, create) {
  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");
  std::shared_ptr<Database> db(new Database(dc));
  RequestStorage * rs(new RequestStorage(db));
  pthread_mutex_t rslock(PTHREAD_MUTEX_INITIALIZER);

  ClientThreadParameters cwp(rs, &rslock);
  EXPECT_FALSE(cwp.connectionAvailable());
  EXPECT_EQ(cwp.getStorage(), rs);
  EXPECT_EQ(-1, cwp.getConnection());
  delete rs;
}

TEST(ClientWorkerParameters, connection) {
  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");
  std::shared_ptr<Database> db(new Database(dc));
  RequestStorage* rs(new RequestStorage(db));
  pthread_mutex_t rslock(PTHREAD_MUTEX_INITIALIZER);

  ClientThreadParameters cwp(rs, &rslock);
  cwp.setConnection(10);
  ASSERT_EQ(10, cwp.getConnection());
  delete rs;
}

/*TEST(ServerAgent, Start) {
  ProxyConfiguration pc;
  pc.setOutPoolCount(1);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  RequestStorage * rs = new RequestStorage(db, pconf->getOutPoolCount());
  ASSERT_TRUE(rs != nullptr);
  ASSERT_TRUE(rs != NULL);
  pthread_mutex_t rs_lock(PTHREAD_MUTEX_INITIALIZER);

  ServerAgent sa(pconf, rs, &rs_lock);
  sa.start();

  delete rs;
}*/

TEST(ClientAgent, CreateClientAgent) {
  ProxyConfiguration pc;
  pc.setInPoolCount(2);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  RequestStorage * rs(new RequestStorage(db));
  pthread_mutex_t rs_lock(PTHREAD_MUTEX_INITIALIZER);

  ClientAgent client(pconf, rs, &rs_lock);
  delete rs;
}

TEST(ClientAgent, CreateClientAgentNoThreads) {
  ProxyConfiguration pc;
  pc.setInPoolCount(0);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  RequestStorage * rs(new RequestStorage(db));
  pthread_mutex_t rs_lock(PTHREAD_MUTEX_INITIALIZER);

  ClientAgent sa(pconf, rs, &rs_lock);
  delete rs;
}

TEST(ClientAgent, CreateClientAgentNegativeThreads) {
  ProxyConfiguration pc;
  ASSERT_FALSE(pc.setOutPoolCount(-2));
  ASSERT_EQ(0, pc.getOutPoolCount());

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(new Database(dc));
  RequestStorage * rs(new RequestStorage(db));
  pthread_mutex_t rs_lock(PTHREAD_MUTEX_INITIALIZER);

  ClientAgent sa(pconf, rs, &rs_lock);
  delete rs;
}

/*TEST(ClientAgent, Start) {
  ProxyConfiguration pc;
  pc.setInPoolCount(1);
  pc.setInPoolPort(8080);
  pc.setInBacklog(10);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(std::make_shared<Database>(dc));
  RequestStorage * rs(new RequestStorage(db));
  pthread_mutex_t rs_lock(PTHREAD_MUTEX_INITIALIZER);

  std::cout << "Create Client Agent" << std::endl;
  ClientAgent ca(pconf, rs, &rs_lock);
  std::cout << "Start Client Agent" << std::endl;
  ca.start();
  delete rs;
}*/

TEST(Proxy, SetUp) {
  ProxyConfiguration pc;
  pc.setInPoolCount(1);
  pc.setInPoolPort(8080);
  pc.setInBacklog(10);
  pc.setOutPoolCount(1);

  DatabaseConfiguration dc;
  dc.setUri("localhost");
  dc.setUser("test");
  dc.setDb("crawlcheck");

  std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(pc));
  std::shared_ptr<Database> db(std::make_shared<Database>(dc));
  RequestStorage * rs(new RequestStorage(db));
  pthread_mutex_t rs_lock(PTHREAD_MUTEX_INITIALIZER);

  ClientAgent * ca = new ClientAgent(pconf, rs, &rs_lock);
  ServerAgent * sa = new ServerAgent(pconf, rs, &rs_lock);

  int pid;
  switch (pid = fork()) {
  case -1: HelperRoutines::error("Fork client & server"); break;
  case 0:
    std::cout << "ClientAgent PID:"<<getpid()<<std::endl;
    ca->start();

    break;
  default:
    std::cout << "ServerAgent PID:"<<getpid()<<std::endl;
    sa->start();
    break;
  }
}


