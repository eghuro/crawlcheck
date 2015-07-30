// Copyright 2015 Alexandr Mansurov

#include <vector>
#include "../src/proxy/HttpParser.h"
#include "gtest/gtest.h"

TEST(HttpParserResult, CreateRequest) {
  HttpParserResult r(HttpParserResultState::REQUEST);
  ASSERT_TRUE(r.isRequest());
  ASSERT_FALSE(r.isResponse());
}

TEST(HttpParserResult, CreateResponse) {
  HttpParserResult r(HttpParserResultState::RESPONSE);
  ASSERT_TRUE(r.isResponse());
  ASSERT_FALSE(r.isRequest());
}

TEST(HttpParserResult, CreateContinue) {
  HttpParserResult r(HttpParserResultState::CONTINUE);
  ASSERT_FALSE(r.isRequest());
  ASSERT_FALSE(r.isResponse());
}

TEST(HttpParserResult, RequestUri) {
  HttpParserResult r1(HttpParserResultState::REQUEST);
  std::string uri = "http://olga.majling.eu;";
  r1.setRequestUri(uri);
  ASSERT_EQ(uri, r1.getRequestUri());

  HttpParserResult r2(HttpParserResultState::RESPONSE);
  // r2.setRequestUri(uri); assertion failed
}

const std::string uri = "http://olga.majling.eu";
TEST(HttpParser, GetRelative) {
  HttpParser parser;

  const std::string request0 = "GET / HTTP/1.1\r\nHost: olga.majling.eu\r\n\r\n";
  // The absoluteURI form is REQUIRED when the request is being made to a proxy.
  auto result = parser.parse(request0);
  ASSERT_FALSE(result.isRequest());
  ASSERT_FALSE(result.isResponse());
}

TEST(HttpParser, GetAbsolute) {
  HttpParser parser;

  const std::string request1 = "GET http://olga.majling.eu HTTP/1.1\r\n\r\n";
  auto result = parser.parse(request1);

  ASSERT_TRUE(result.isRequest());
  ASSERT_FALSE(result.isResponse());

  ASSERT_TRUE(uri == result.getRequestUri());
}

TEST(HttpParser, Methods) {
  std::vector<std::string> methods;
  methods.push_back("GET");
  methods.push_back("HEAD");
  methods.push_back("POST");
  methods.push_back("PUT");
  methods.push_back("DELETE");
  methods.push_back("TRACE");
  methods.push_back("CONNECT");

  for(auto method : methods) {
    HttpParser p;
    auto result = p.parse(method+" http://kdmanalytics.com/about.html HTTP/1.1\r\nPragma:no-cache\r\n\r\n");

    ASSERT_TRUE(result.isRequest());
    ASSERT_FALSE(result.isResponse());

    ASSERT_TRUE(result.getRequestUri() == "http://kdmanalytics.com/about.html");
  }
}

TEST(HttpParser, VariousUris) {
  std::vector<std::string> uris;
  uris.push_back("http://olga.majling.eu/Vyuka");
  uris.push_back("http://tvprogram.idnes.cz");
  uris.push_back("http://intercitybuslanzarote.es");

  HttpParser parser;
  for (auto uri : uris) {;
    auto result = parser.parse("GET "+uri+" HTTP/1.1\r\n\r\n");

    ASSERT_TRUE(result.isRequest());
    ASSERT_FALSE(result.isResponse());

    ASSERT_TRUE(uri == result.getRequestUri());
  }
}

TEST(HttpParser, RawRequest) {
  HttpParser parser;
  const std::string request = "GET http://olga.majling.eu HTTP/1.1\r\n\r\n";
  auto result = parser.parse(request);
  ASSERT_TRUE(request == result.getRawRequest());
}

TEST(HttpParser, ChunkedRequest) {
  HttpParser parser;
  const std::string chunk0 = "GET http:/";
  const std::string chunk1 = "/olga.majl";
  const std::string chunk2 = "ing.eu HTT";
  const std::string chunk3 = "P/1.1\r\n\r\n";

  auto result0 = parser.parse(chunk0);
  ASSERT_TRUE(result0.doContinue());

  auto result1 = parser.parse(chunk1);
  ASSERT_TRUE(result1.doContinue());

  auto result2 = parser.parse(chunk2);
  ASSERT_TRUE(result2.doContinue());

  auto result3 = parser.parse(chunk3);
  ASSERT_FALSE(result3.doContinue());
  ASSERT_FALSE(result3.isResponse());
  ASSERT_TRUE(result3.isRequest());
  ASSERT_TRUE("http://olga.majling.eu" == result3.getRequestUri());
  ASSERT_TRUE("GET http://olga.majling.eu HTTP/1.1\r\n\r\n" == result3.getRawRequest());
}

TEST(HttpParser, Response) {

}
