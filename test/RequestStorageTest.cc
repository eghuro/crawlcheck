// Copyright 2015 Alexandr Mansurov

#include <memory>
#include "../src/proxy/RequestStorage.h"
#include "../src/proxy/HttpParser.h"
#include "../src/proxy/db.h"
#include "gtest/gtest.h"

TEST(RequestStorage, Request) {
  DatabaseConfiguration dbc;
  dbc.setUri("localhost");
  dbc.setUser("test");
  dbc.setDb("crawlcheck");
  std::shared_ptr<Database> db = std::make_shared<Database>(dbc);
  RequestStorage rs(db);
  ASSERT_FALSE(rs.requestAvailable());

  HttpParserResult request(HttpParserResultState::REQUEST);
  request.setMethod(RequestMethod::GET);
  auto id = rs.insertRequest(request);
  ASSERT_TRUE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable(id));

  auto retrieved = rs.retrieveRequest();
  ASSERT_FALSE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable(id));
  ASSERT_TRUE(std::get<0>(retrieved).isRequest());
  ASSERT_TRUE(std::get<0>(retrieved).getMethod() == RequestMethod::GET);
  ASSERT_TRUE(std::get<0>(retrieved) == request);
  ASSERT_TRUE(id == std::get<1>(retrieved));
}

TEST(RequestStorage, Response) {
  DatabaseConfiguration dbc;
  dbc.setUri("localhost");
  dbc.setUser("test");
  dbc.setDb("crawlcheck");
  std::shared_ptr<Database> db = std::make_shared<Database>(dbc);
  RequestStorage rs(db);
  ASSERT_FALSE(rs.requestAvailable());

  HttpParserResult response(HttpParserResultState::RESPONSE);
  rs.insertResponse(response, 0);
  ASSERT_TRUE(rs.responseAvailable(0));
  ASSERT_FALSE(rs.requestAvailable());

  auto retrieved = rs.retrieveResponse(0);
  ASSERT_FALSE(rs.requestAvailable());
  ASSERT_FALSE(rs.responseAvailable(0));
  ASSERT_TRUE(response.getRaw() == retrieved);
}
