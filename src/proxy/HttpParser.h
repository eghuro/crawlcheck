// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HTTPPARSER_H_
#define SRC_PROXY_HTTPPARSER_H_

#include <unistd.h>
#include <memory>
#include <string>
#include <deque>
#include <regex>
#include <iostream>
#include <cassert>

enum HttpParserResultState {
  CONTINUE, REQUEST, RESPONSE
};

enum HttpParserState {
  START
};

class HttpParserResult {
 public:
  explicit HttpParserResult(HttpParserResultState state):state_(state),
    request_uri() {}
  virtual ~HttpParserResult() {}

  inline bool isRequest() const {
    return state_ == HttpParserResultState::REQUEST;
  }

  inline bool isResponse() const {
    return state_ == HttpParserResultState::RESPONSE;
  }

  inline std::string getRequestUri() const {
    assert(state_ == HttpParserResultState::REQUEST);
    return request_uri;
  }

  inline void setRequestUri(const std::string & uri) {
    assert(state_ == HttpParserResultState::REQUEST);
    request_uri = uri;
  }

 private:
  const HttpParserResultState state_;
  std::string request_uri;
};

class HttpParser {
 public:
  HttpParser():state_(HttpParserState::START) {}
  virtual ~HttpParser() {}

  HttpParserResult parse(const std::string & chunk) {
    const std::string reg("[GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT]{1} http://[a-zA-Z0-9./]+ HTTP/1.1\r\n([a-zA-Z: -]+\r\n)*\r\n");

    std::cout << reg << std::endl<<chunk<<std::endl;
    std::regex re(reg);
    if(std::regex_match(chunk,re)) {
      HttpParserResult result(HttpParserResultState::REQUEST);
      result.setRequestUri("http://olga.majling.eu");
      return result;
    } else {
      std::cout << "Not matched" <<std::endl;
    }

    return HttpParserResult(HttpParserResultState::CONTINUE);
  }

 private:
  HttpParserState state_;
};
#endif  // SRC_PROXY_HTTPPARSER_H_
