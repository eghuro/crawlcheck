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


TEST(HttpParserResult, Equality) {
  HttpParserResult r1(HttpParserResultState::INVALID);
  HttpParserResult r2(HttpParserResultState::INVALID);
  ASSERT_FALSE(r1 == r2);

  HttpParserResult r3(HttpParserResultState::CONTINUE);
  HttpParserResult r4(HttpParserResultState::CONTINUE);
  ASSERT_FALSE(r1 == r3);
  ASSERT_TRUE(r3 == r4);

  HttpParserResult r5(HttpParserResultState::REQUEST);
  HttpParserResult r6(HttpParserResultState::REQUEST);
  r5.setRaw("bflmpsvz");
  r6.setRaw("hchkrdtn");
  ASSERT_TRUE(r5 == r5);
  ASSERT_FALSE(r5 == r3);
  ASSERT_FALSE(r5 == r2);
  ASSERT_FALSE(r5 == r6);
  r6.setRaw(r5.getRaw());
  ASSERT_TRUE(r5 == r6);

  HttpParserResult r7(HttpParserResultState::RESPONSE);
  HttpParserResult r8(HttpParserResultState::RESPONSE);
  r7.setRaw("bflmpsvz");
  r8.setRaw("hchkrdtn");
  ASSERT_TRUE(r7 == r7);
  ASSERT_FALSE(r7 == r2);
  ASSERT_FALSE(r7 == r4);
  ASSERT_FALSE(r7 == r5);
  ASSERT_FALSE(r7 == r8);
  r8.setRaw(r7.getRaw());
  ASSERT_TRUE(r7 == r8);
}
const std::string uri = "http://olga.majling.eu";
TEST(RequestParser, GetRelative) {
  HttpParser parser;

  const std::string req = "GET / HTTP/1.1\r\nHost: olga.majling.eu\r\n\r\n";
  // The absoluteURI form is REQUIRED when the request is being made to a proxy.
  auto result = parser.parse(req);
  ASSERT_FALSE(result.isRequest());
  ASSERT_FALSE(result.isResponse());
}

TEST(RequestParser, GetAbsolute) {
  HttpParser parser;

  const std::string request1 = "GET http://olga.majling.eu HTTP/1.1\r\n\r\n";
  auto result = parser.parse(request1);

  ASSERT_TRUE(result.isRequest());
  ASSERT_FALSE(result.isResponse());

  ASSERT_TRUE(uri == result.getRequestUri());
}

TEST(RequestParser, Methods) {
  std::vector<std::string> methods;
  methods.push_back("GET");
  methods.push_back("HEAD");
  methods.push_back("POST");
  methods.push_back("PUT");
  methods.push_back("DELETE");
  methods.push_back("TRACE");
  methods.push_back("CONNECT");

  std::ostringstream oss;
  oss << " http://kdmanalytics.com/about.html HTTP/1.1\r\n";
  oss << "Pragma:no-cache\r\n\r\n";
  for (auto method : methods) {
    HttpParser p;

    auto result = p.parse(method+oss.str());

    ASSERT_TRUE(result.isRequest());
    ASSERT_FALSE(result.isResponse());

    ASSERT_EQ(result.getRequestUri(), "http://kdmanalytics.com/about.html");
  }
}

TEST(RequestParser, VariousUris) {
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

TEST(RequestParser, RawRequest) {
  HttpParser parser;
  const std::string request = "GET http://olga.majling.eu HTTP/1.1\r\n\r\n";
  auto result = parser.parse(request);
  ASSERT_TRUE(request == result.getRaw());
}

/*TEST(RequestParser, ChunkedRequest) {
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
  ASSERT_TRUE("GET http://olga.majling.eu HTTP/1.1\r\n\r\n" == result3.getRaw());
}

TEST(RequestParser, ComplexUrisRequest) {
  // TODO(alex): test all sort of acceptable URIs
}*/

TEST(RequestParser, RequestPortImplicit) {
  HttpParser parser;
  const std::string request = "GET http://olga.majling.eu HTTP/1.1\r\n\r\n";
  auto result = parser.parse(request);
  ASSERT_TRUE(80 == result.getPort());
}

TEST(RequestParser, RequestPortExplicit) {
  HttpParser parser;
  const std::string request = "GET http://poseidon.eghuro.cz:3333/login HTTP/1.1\r\n\r\n";
  auto result = parser.parse(request);
  ASSERT_TRUE(3333 == result.getPort());
}

TEST(ResponseParser, ResponseIdentification) {
  HttpParser parser;
  std::ostringstream oss;
  oss << "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n";
  oss << "Content-Type: text/html; charset=ISO-8859-4\r\n\r\n";
  oss << "<html></html>";

  auto result = parser.parse(oss.str());

  ASSERT_TRUE(result.isResponse());
  ASSERT_FALSE(result.doContinue());
  ASSERT_FALSE(result.isRequest());
}

TEST(ResponseParser, ResponseStatus) {
  HttpParser parser;

  std::ostringstream oss;
  oss << "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n";
  oss << "Content-Type: text/html; charset=ISO-8859-4\r\n\r\n<html></html>";

  auto result = parser.parse(oss.str());

  ASSERT_TRUE(result.getStatus() == HttpResponseStatus(200));
}

TEST(ResponseParser, ResponseContent) {
  HttpParser parser;

  std::ostringstream oss;
  oss << "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n";
  oss << "Content-Type: text/html; charset=ISO-8859-4\r\n\r\n";
  oss << "<html></html>";

  auto result = parser.parse(oss.str());

  ASSERT_EQ(result.getContentType(), "text/html");
  ASSERT_EQ(result.getContent(), "<html></html>");
}

TEST(ResponseParser, RawResponse) {
  HttpParser parser;
  std::ostringstream oss;
  oss << "HTTP/1.1 200 OK\r\nContent-Length: 13\r\n";
  oss << "Content-Type: text/html; charset=ISO-8859-4\r\n\r\n";
  oss << "<html></html>";

  auto result = parser.parse(oss.str());

  ASSERT_TRUE(result.getRaw() == oss.str());
}
