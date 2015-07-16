/*
 * RequestStorage.h
 *
 *  Created on: Jul 16, 2015
 *      Author: alex
 */

#ifndef SRC_PROXY_REQUESTSTORAGE_H_
#define SRC_PROXY_REQUESTSTORAGE_H_

#include <memory>
#include <string>
#include <sstream>
#include "./HttpParser.h"

class HttpRequestFactory {
 public:
  static std::string createHttpRequest(HttpParserResult result) {
	  std::ostringstream stream;
	  // TODO(alex): create the request
	  return stream.str();
  }
};

class RequestStorage {
 public:
  RequestStorage() : results() {};
  virtual ~RequestStorage() {};

  // TODO(alex): zamky!!
  void insertParserResult(const HttpParserResult & result) {
    results.push_back(result);
  }
  std::string retrieveRequest() {
    auto result = results.front();
    std::string request = HttpRequestFactory::createHttpRequest(result);
    results.pop_front();
    return request;
  }
 private:
  std::deque<HttpParserResult> results;
};

#endif /* SRC_PROXY_REQUESTSTORAGE_H_ */
