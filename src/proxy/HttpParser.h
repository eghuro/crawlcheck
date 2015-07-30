// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HTTPPARSER_H_
#define SRC_PROXY_HTTPPARSER_H_

#include <unistd.h>
#include <errno.h>
#include <memory>
#include <string>
#include <deque>
#include <regex>
#include <iostream>
#include <cassert>
#include "./HelperRoutines.h"

enum HttpParserResultState {
  CONTINUE, REQUEST, RESPONSE
};

enum HttpParserState {
  START
};

class HttpParserResult {
 public:
  explicit HttpParserResult(HttpParserResultState state):state_(state),
    request_uri(), request_string() {}
  virtual ~HttpParserResult() {}

  inline bool doContinue() const {
    return state_ == HttpParserResultState::CONTINUE;
  }

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

  inline void setRawRequest(const std::string & request) {
    assert(state_ == HttpParserResultState::REQUEST);
    request_string = request;
  }

  inline std::string getRawRequest() const {
    assert(state_ == HttpParserResultState::REQUEST);
    return request_string;
  }

 private:
  const HttpParserResultState state_;
  std::string request_uri, request_string;
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
          result.setRawRequest(chunk);
          return result;
        }
      }
    } else {
      errno = EINVAL;
      HelperRoutines::warning("Error while parsing input");
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
