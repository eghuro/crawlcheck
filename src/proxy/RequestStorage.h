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
#include "pthread.h"
#include "./HttpParser.h"
#include "./HelperRoutines.h"

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
  RequestStorage() : results(), results_mutex(PTHREAD_MUTEX_INITIALIZER) {};
  virtual ~RequestStorage() {};

  void insertParserResult(const HttpParserResult & result) {
    if (pthread_mutex_lock(&results_mutex) == 0) {
      results.push_back(result);
      if (pthread_mutex_unlock(&results_mutex) == 0) {
    	  HelperRoutines::warning("Cannot unlock mutex on a request storage.");
      }
    } else {
      HelperRoutines::warning("Cannot lock mutex on a request storage.");
    }
  }

  std::string retrieveRequest() {
	if (pthread_mutex_lock(&results_mutex) == 0) {
      auto result = results.front();
      results.pop_front();
      if (pthread_mutex_unlock(&results_mutex) != 0) {
    	  HelperRoutines::warning("Cannot unlock mutex on a request storage.");
      }

      std::string request = HttpRequestFactory::createHttpRequest(result);
      return request;
	} else {
	  HelperRoutines::warning("Cannot lock mutex on a request storage.");
	}
    return "";  // TODO(alex): exception?
  }

  std::string retrieveResponse() {
    return "";
  }

  bool responseAvailable() {
    return false;
  }

  bool done() {
    return false;
  }
 private:
  std::deque<HttpParserResult> results;
  pthread_mutex_t results_mutex;
};

#endif /* SRC_PROXY_REQUESTSTORAGE_H_ */
