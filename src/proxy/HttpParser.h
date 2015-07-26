// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HTTPPARSER_H_
#define SRC_PROXY_HTTPPARSER_H_

#include <memory>
#include <string>
#include <deque>
#include <regex>
#include <iostream>
#include <unistd.h>

enum HttpParserResultState {
  CONTINUE, REQUEST
};

enum HttpParserState {
  START
};

class HttpParserResult {
 public:
  explicit HttpParserResult(HttpParserResultState state):state_(state),
    request_uri() {}
  virtual ~HttpParserResult() {}

  bool inline request() const {
    return state_ == HttpParserResultState::REQUEST;
  }

  std::string inline getRequestUri() const {
    return request_uri;
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
    //write(1, chunk.c_str(), chunk.size());

    std::smatch sm;
    std::regex re("([A-Z]+) ([a-zA-Z0-9:/]+) HTTP/1.1\r\n");
    std::regex_match(chunk.cbegin(), chunk.cend(), sm, re);
    for (auto it = sm.cbegin(); it != sm.cend(); ++it) {
    	std::cout << *it << std::endl;
    }

    return HttpParserResult(HttpParserResultState::CONTINUE);
  }

 private:
  HttpParserState state_;
};
#endif  // SRC_PROXY_HTTPPARSER_H_
