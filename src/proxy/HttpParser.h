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
#include <map>
#include <utility>
#include "./HelperRoutines.h"

enum HttpParserResultState {
  CONTINUE, REQUEST, RESPONSE, INVALID
};

enum HttpParserState {
  START
};

class HttpResponseStatus {
 public:
  explicit HttpResponseStatus(std::size_t code):status_code(code) {}

  inline bool operator==(std::size_t code) {
    return code == status_code;
  }

  inline bool operator==(const HttpResponseStatus & status) {
    return status.getCode() == status_code;
  }

  inline std::size_t getCode() const {
    return status_code;
  }
 private:
  std::size_t status_code;
};

class HttpParserResult {
 public:
  explicit HttpParserResult(HttpParserResultState state = HttpParserResultState::INVALID):state_(state),
    request_uri(), raw_message(), content_type(), content(),
    response_status(0) {}
  virtual ~HttpParserResult() {}

  bool operator==(const HttpParserResult & result) {
    switch(state_) {
    case HttpParserResultState::INVALID : return false;
    case HttpParserResultState::CONTINUE:
      return result.doContinue();
    case HttpParserResultState::REQUEST:
      if (result.isRequest()) {
        return result.getRaw() == getRaw();
      } else {
        return false;
      }
    case HttpParserResultState::RESPONSE:
      if(result.isResponse()) {
        return result.getRaw() == getRaw();
      } else {
        return false;
      }
    default: assert(false);
    }
  }

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

  inline void setRaw(const std::string & request) {
    assert((state_ == HttpParserResultState::REQUEST) ||
        (state_ == HttpParserResultState::RESPONSE));
    raw_message = request;
  }

  inline std::string getRaw() const {
    assert((state_ == HttpParserResultState::REQUEST) ||
                (state_ == HttpParserResultState::RESPONSE));
    return raw_message;
  }

  inline void setResponseStatus(const HttpResponseStatus & status) {
    assert((state_ == HttpParserResultState::REQUEST) ||
            (state_ == HttpParserResultState::RESPONSE));
    response_status = status;
  }

  inline HttpResponseStatus getStatus() const {
    assert(state_ == HttpParserResultState::RESPONSE);
    return response_status;
  }

  inline void setContentType(const std::string & ctype) {
    assert(state_ == HttpParserResultState::RESPONSE);
    content_type = ctype;
  }

  inline std::string getContentType() const {
    assert(state_ == HttpParserResultState::RESPONSE);
    return content_type;
  }

  inline void setContent(const std::string & cont) {
    assert(state_ == HttpParserResultState::RESPONSE);
    content = cont;
  }

  inline std::string getContent() const {
    assert(state_ == HttpParserResultState::RESPONSE);
    return content;
  }

  inline void setPort(std::size_t port) {
    assert((state_ == HttpParserResultState::REQUEST) ||
                (state_ == HttpParserResultState::RESPONSE));
    HttpParserResult::port = port;
  }

  inline std::size_t getPort() const {
    assert((state_ == HttpParserResultState::REQUEST) ||
                (state_ == HttpParserResultState::RESPONSE));
    return port;
  }

 private:
  const HttpParserResultState state_;
  std::string request_uri, raw_message, content_type, content;
  HttpResponseStatus response_status;
  std::size_t port;
};

class HttpParser {
 public:
  HttpParser():state_(HttpParserState::START) {}
  virtual ~HttpParser() {}

  HttpParserResult parse(const std::string & chunk) {
    std::ostringstream oss_req;
    oss_req << "(GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT) ";
    oss_req << "http://([a-zA-Z0-9]([./])?)+ ";
    oss_req << "HTTP/1.1\r\n([a-zA-Z0-9: -]+\r\n)*\r\n";

    std::ostringstream oss_res;
    oss_res << "HTTP/1.1 ([0-9]){3} [a-z A-Z -]+\r\n";
    oss_res << "([a-zA-Z0-9: -/;=]+\r\n)*\r\n.*";

    const std::regex req(oss_req.str());
    const std::regex res(oss_res.str());

    if (std::regex_match(chunk, req)) {
      HttpParserResult result(HttpParserResultState::REQUEST);

      auto begin = findSpace(chunk, 0);
      if (begin != -1) {
        begin++;  // zacatek adresy na znaku po 1. mezere - viz regex

        int end = findSpace(chunk, begin);
        if (end != -1) {
          auto length = end-begin;
          std::string uri = chunk.substr(begin, length);
          result.setRequestUri(uri);
          result.setRaw(chunk);
          return result;
        }
      }
    } else if (std::regex_match(chunk, res)) {
      HttpParserResult result(HttpParserResultState::RESPONSE);

      // status
      auto begin = findSpace(chunk, 0);
      if (begin != -1) {
        begin++;

        auto end = findSpace(chunk, begin);
        if (end != -1) {
          auto length = end-begin;
          int code = std::stoi(chunk.substr(begin, length));
          result.setResponseStatus(HttpResponseStatus(code));

          // headers
          begin = findCRLF(chunk, end)+2;
          end = findDoubleCRLF(chunk, begin);

          if (end != -1) {
            auto headers_unparsed = chunk.substr(begin, end-begin+2);

            auto headers = parseHeaders(headers_unparsed);
            transformHeadersToResults(headers, result);

            // body
            end+=4;  // CRLFCRLF
            result.setContent(chunk.substr(end, chunk.length()-end));

            result.setRaw(chunk);
            return result;
          }
        }
      }  // response
    } else {
      errno = EINVAL;
      HelperRoutines::warning("Error while parsing input");
    }

    return HttpParserResult(HttpParserResultState::CONTINUE);
  }

 private:
  HttpParserState state_;

  inline int findSpace(const std::string & chunk, std::size_t start) const {
    std::size_t pos = start;
    while (pos < chunk.length()) {
      if (chunk[pos] != ' ') {
        pos++;
      } else {
        return pos;
      }
    }
    return -1;
  }

  inline int findCRLF(const std::string & chunk, std::size_t start) const {
    std::size_t pos = start;
    while (pos < chunk.length()) {
      if (chunk[pos] != '\r') {
        pos++;
      } else if (chunk[pos+1] == '\n') {
        return pos;
      } else {  // CR without LF after
        pos++;
      }
    }
    return -1;
  }

  inline int findDoubleCRLF(const std::string & chunk, std::size_t start)
  const {
    std::size_t pos = start;
    while (pos < chunk.length()) {
      if (doubleCRLF(chunk, pos)) {
        pos++;
      } else {  // CR without LF after
        return pos;
      }
    }
    return -1;
  }

  inline bool doubleCRLF(const std::string & chunk, std::size_t pos) const {
    return (chunk[pos] != '\r') || (chunk[pos+1] != '\n') ||
        (chunk[pos+2] != '\r') || (chunk[pos+3] != '\n');
  }

  inline int findDash(const std::string & chunk, std::size_t start) const {
    std::size_t pos = start;
    while (pos < chunk.length()) {
      if (chunk[pos] != ':') {
        pos++;
      } else {
        return pos;
      }
    }
    return -1;
  }

  typedef std::pair<std::string, std::string> record;
  typedef std::map<std::string, std::string> storage;

  inline record splitHeader(const std::string & header) const {
    auto separatorPos = findDash(header, 0);
    if (separatorPos == -1) return record("", "");
    auto keyLength = separatorPos;
    auto valueLength = header.length() - separatorPos-1;
    return record(header.substr(0, keyLength),
        header.substr(separatorPos+2, valueLength));
  }

  inline storage parseHeaders(const std::string & headers) const {
    storage parsed_headers;

    int pos = 0;
    while (pos <= static_cast<int>(headers.length())) {
      auto headerEnd = findCRLF(headers, pos);
      if (headerEnd != -1) {
        auto headerLength = headerEnd - pos;

        auto headerPair = splitHeader(headers.substr(pos, headerLength));
        pos += headerLength+2;

        parsed_headers.insert(headerPair);
      } else {
        pos = static_cast<int>(headers.length()) +1;
      }
    }

    return parsed_headers;
  }

  inline void transformHeadersToResults(const storage & headers,
      HttpParserResult & results) {
    auto it = headers.find("Content-Type");
    if (it != headers.end()) {
      std::string ct = it->second;
      std::string cut;
      for (std::size_t i = 0; i < ct.length(); i++) {
        if (ct[i] == ';') {
          cut = ct.substr(0, i);
          break;
        }
      }
      results.setContentType(cut);
    }
  }
};
#endif  // SRC_PROXY_HTTPPARSER_H_
