// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HTTPPARSER_H_
#define SRC_PROXY_HTTPPARSER_H_

#include <memory>
#include <string>
#include <deque>

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

  bool request() const {
    return state_ == HttpParserResultState::REQUEST;
  }

  std::string getRequestUri() const {
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
    return HttpParserResult(HttpParserResultState::CONTINUE);
  }

 private:
  HttpParserState state_;
};
#endif  // SRC_PROXY_HTTPPARSER_H_
