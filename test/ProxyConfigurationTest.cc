// Copyright 2015 Alexandr Mansurov

#include <sys/socket.h>
#include "../src/proxy/ProxyConfiguration.h"
#include "gtest/gtest.h"

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
  ASSERT_EQ(1, pc.getInBacklog());

  ASSERT_FALSE(pc.setInBacklog(-10));

  ASSERT_EQ(1, pc.getInBacklog());
  int x = SOMAXCONN + 1;
  EXPECT_TRUE(pc.setInBacklog(x));
  ASSERT_EQ(SOMAXCONN, pc.getInBacklog());
}
