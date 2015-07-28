// Copyright 2015 Alexandr Mansurov

#include <sys/socket.h>
#include "../src/proxy/ProxyConfiguration.h"
#include "gtest/gtest.h"

TEST(ProxyConfiguration, PoolCount) {
  ProxyConfiguration pc;

  EXPECT_EQ(0, pc.getPoolCount());
  bool b1 = pc.setPoolCount(10);
  EXPECT_TRUE(b1);
  ASSERT_EQ(10, pc.getPoolCount());

  ASSERT_FALSE(pc.setPoolCount(-1));
  EXPECT_EQ(10, pc.getPoolCount());

  bool b2 = pc.setPoolCount(0);
  EXPECT_TRUE(b2);
  ASSERT_EQ(0, pc.getPoolCount());
}

TEST(ProxyConfiguration, MaxIn) {
  ProxyConfiguration pc;

  EXPECT_EQ(0, pc.getMaxIn());
  bool b1 = pc.setMaxIn(10);
  EXPECT_TRUE(b1);
  ASSERT_EQ(10, pc.getMaxIn());

  ASSERT_FALSE(pc.setMaxIn(-1));
  EXPECT_EQ(10, pc.getMaxIn());

  bool b2 = pc.setMaxIn(0);
  EXPECT_TRUE(b2);
  ASSERT_EQ(0, pc.getMaxIn());
}

TEST(ProxyConfiguration, MaxOut) {
  ProxyConfiguration pc;

  EXPECT_EQ(0, pc.getMaxOut());
  bool b1 = pc.setMaxOut(10);
  EXPECT_TRUE(b1);
  ASSERT_EQ(10, pc.getMaxOut());

  ASSERT_FALSE(pc.setMaxOut(-1));
  EXPECT_EQ(10, pc.getMaxOut());

  bool b2 = pc.setMaxOut(0);
  EXPECT_TRUE(b2);
  ASSERT_EQ(0, pc.getMaxOut());
}

TEST(ProxyConfiguration, InPort) {
  ProxyConfiguration pc;

  EXPECT_EQ(-1, pc.getInPoolPort());
  EXPECT_FALSE(pc.setInPoolPort(0));
  EXPECT_TRUE(pc.setInPoolPort(1));

  ASSERT_TRUE(pc.setInPoolPort(80));
  ASSERT_EQ(80, pc.getInPoolPort());
  ASSERT_EQ("80", pc.getInPortString());
  ASSERT_TRUE(pc.setInPoolPort(8080));
  ASSERT_TRUE(pc.setInPoolPort(8081));
  ASSERT_TRUE(pc.setInPoolPort(1080));
  ASSERT_TRUE(pc.setInPoolPort(3346));

  ASSERT_FALSE(pc.setInPoolPort(65536));
  EXPECT_EQ(3346, pc.getInPoolPort());
  EXPECT_TRUE(pc.setInPoolPort(65535));
  ASSERT_FALSE(pc.setInPoolPort(1000000));
}

TEST(ProxyConfiguration, InBacklog) {
  ProxyConfiguration pc;

  EXPECT_EQ(-1, pc.getInBacklog());

  EXPECT_TRUE(pc.setInBacklog(0));
  ASSERT_TRUE(pc.setInBacklog(1));
  ASSERT_EQ(1,pc.getInBacklog());

  ASSERT_FALSE(pc.setInBacklog(-10));

  ASSERT_EQ(1,pc.getInBacklog());
  int x = SOMAXCONN + 1;
  EXPECT_TRUE(pc.setInBacklog(x));
  ASSERT_EQ(SOMAXCONN, pc.getInBacklog());
}

TEST(ProxyConfiguration, DbcFd) {
  ProxyConfiguration pc;

  EXPECT_EQ(-1, pc.getDbcFd());

  EXPECT_TRUE(pc.setDbcFd(0));  // stdin
  EXPECT_TRUE(pc.setDbcFd(1));  // stdout
  EXPECT_TRUE(pc.setDbcFd(2));  // stderr

  ASSERT_TRUE(pc.setDbcFd(13));
  ASSERT_EQ(13, pc.getDbcFd());

  ASSERT_FALSE(pc.setDbcFd(-1));
  ASSERT_EQ(13, pc.getDbcFd());
}
