// Copyright 2015 Alexandr Mansurov

#include "../src/db/db.h"
#include "../src/proxy/HttpParser.h"
#include "gtest/gtest.h"

TEST(DatabaseConfiguration, BasicCheck) {

}

TEST(DatabaseAPI, ClientRequest) {
  DatabaseConfiguration dbc;
  dbc.setUser("test");
  dbc.setDb("crawlcheck");
  Database db(dbc);

  HttpParserResult request(HttpParserResultState::REQUEST);
  request.setRequestUri(HttpUriFactory::createUri("http://www.mff.cuni.cz"));
  request.setMethod(RequestMethod::GET);

  auto count = db.getClientRequestCount();
  auto request_id = db.setClientRequest(request);
  auto count1 = db.getClientRequestCount();
  ASSERT_TRUE(count+1 == count1);
  ASSERT_TRUE(request == db.getClientRequest(request_id));
}

TEST(DatabaseAPI, ServerResponse) {
  DatabaseConfiguration dbc;
  dbc.setUser("test");
  dbc.setDb("crawlcheck");
  Database db(dbc);

  HttpParserResult request(HttpParserResultState::REQUEST);
  request.setRequestUri(HttpUriFactory::createUri("http://www.mff.cuni.cz"));
  request.setMethod(RequestMethod::GET);

  auto id = db.setClientRequest(request);

  HttpParserResult response(HttpParserResultState::RESPONSE);
  response.setResponseStatus(HttpResponseStatus(200));
  response.setContentType("text/html");
  response.setContent("<html>\n</html>");

  auto count = db.getServerResponseCount();
  db.setServerResponse(id, response);

  ASSERT_TRUE(count+1 == db.getServerResponseCount());
  ASSERT_TRUE(response == db.getServerResponse(id));
}


