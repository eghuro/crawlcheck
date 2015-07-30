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
    const std::string reg("(GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT) http://([a-zA-Z0-9]([./])?)+ HTTP/1.1\r\n([a-zA-Z: -]+\r\n)*\r\n");

    std::regex re(reg);
    if(std::regex_match(chunk,re)) {
      HttpParserResult result(HttpParserResultState::REQUEST);

      auto begin = findSpace(chunk,0);
      if (begin != -1) {
        begin++; // zacatek adresy na znaku po 1. mezere - viz regex

        int end = findSpace(chunk,begin);
        if (end != -1) {
          auto length = end-begin;
          std::string uri = chunk.substr(begin,length);
          result.setRequestUri(uri);
          return result;
        }
      }
    } else {
      std::cout << "Not matched" <<std::endl;
    }

    return HttpParserResult(HttpParserResultState::CONTINUE);
  }

 private:
  HttpParserState state_;

  int findSpace(const std::string & chunk, std::size_t start) const {
    std::size_t pos = start;
    while (pos < chunk.length()) {
      if (chunk[pos] != ' ') {
        pos++;
      } else return pos;
    }
    return -1;
  }
};
#endif  // SRC_PROXY_HTTPPARSER_H_
