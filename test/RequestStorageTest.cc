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
  Database db(dbc);
  db.cleanup();

  RequestStorage rs(dbc);
  EXPECT_FALSE(rs.requestAvailable());

  HttpParserResult request(HttpParserResultState::REQUEST);
  request.setMethod(RequestMethod::GET);
  request.setRequestUri(HttpUriFactory::createUri("http://google.com/"));
  auto id = rs.insertRequest(request);
  EXPECT_TRUE(rs.requestAvailable());
  EXPECT_FALSE(rs.responseAvailable(id));

  auto retrieved = rs.retrieveRequest();
  EXPECT_FALSE(rs.requestAvailable());
  EXPECT_FALSE(rs.responseAvailable(id));
  EXPECT_TRUE(std::get<0>(retrieved).isRequest());
  EXPECT_TRUE(std::get<0>(retrieved).getMethod() == RequestMethod::GET);
  EXPECT_TRUE(std::get<0>(retrieved) == request);
  EXPECT_TRUE(id == std::get<1>(retrieved));
}

TEST(RequestStorage, Response) {
  DatabaseConfiguration dbc;
  dbc.setUri("localhost");
  dbc.setUser("test");
  dbc.setDb("crawlcheck");
  RequestStorage rs(dbc);
  EXPECT_FALSE(rs.requestAvailable());

  HttpParserResult request(HttpParserResultState::REQUEST);
  request.setMethod(RequestMethod::GET);
  request.setRequestUri(HttpUriFactory::createUri("http://google.com/"));
  auto id = rs.insertRequest(request);

  EXPECT_TRUE(rs.requestAvailable());
  rs.retrieveRequest();

  HttpParserResult response(HttpParserResultState::RESPONSE);
  rs.insertResponse(response, id);
  EXPECT_TRUE(rs.responseAvailable(id));
  EXPECT_FALSE(rs.requestAvailable());

  auto retrieved = rs.retrieveResponse(0);
  EXPECT_FALSE(rs.requestAvailable());
  EXPECT_FALSE(rs.responseAvailable(0));
  EXPECT_TRUE(response.getRaw() == retrieved);
}
