// Copyright 2015 Alexandr Mansurov

#include "../src/proxy/RequestStorage.h"
#include "../src/proxy/HttpParser.h"
#include "gtest/gtest.h"

TEST(RequestStorage, Request) {
  RequestStorage rs;
  ASSERT_FALSE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable());

  HttpParserResult request(HttpParserResultState::REQUEST);
  rs.insertParserResult(request, 0);
  ASSERT_TRUE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable());

  auto retrieved = rs.retrieveRequest();
  ASSERT_FALSE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable());
  ASSERT_TRUE(std::get<0>(retrieved) == request);
  ASSERT_TRUE(std::get<1>(retrieved) == 0);
}

TEST(RequestStorage, Response) {
  RequestStorage rs;
  ASSERT_FALSE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable());

  HttpParserResult response(HttpParserResultState::RESPONSE);
  rs.insertParserResult(response,0);
  ASSERT_TRUE(rs.responseAvailable());
  ASSERT_FALSE(rs.requestAvailable());

  auto retrieved = rs.retrieveResponse(0);
  ASSERT_FALSE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable());
  ASSERT_TRUE(response.getRaw() == retrieved);
}