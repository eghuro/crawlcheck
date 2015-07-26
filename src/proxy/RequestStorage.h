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
  // first the request itself, second the uri to connect, third port to connect
  static std::tuple<std::string,std::string, int> createHttpRequest(HttpParserResult result) {
	  std::ostringstream stream;
	  // TODO(alex): create the request
	  return std::tuple<std::string, std::string,int>(stream.str(),"",80);
  }
};

class RequestStorage {
 public:
  typedef std::tuple<std::string, int, std::string, int> request_type;

  RequestStorage() : results(), results_mutex(PTHREAD_MUTEX_INITIALIZER) {};
  virtual ~RequestStorage() {};

  void insertParserResult(const HttpParserResult & result, int id) {
    if (pthread_mutex_lock(&results_mutex) == 0) {
      results.push_back(result);
      if (pthread_mutex_unlock(&results_mutex) == 0) {
    	  HelperRoutines::warning("Cannot unlock mutex on a request storage.");
      }
    } else {
      HelperRoutines::warning("Cannot lock mutex on a request storage.");
    }
  }

  request_type retrieveRequest() {
	if (pthread_mutex_lock(&results_mutex) == 0) {
      auto result = results.front();
      results.pop_front();
      if (pthread_mutex_unlock(&results_mutex) != 0) {
    	  HelperRoutines::warning("Cannot unlock mutex on a request storage.");
      }

      int id = 0;  // TODO(alex): identifiers
      auto request = HttpRequestFactory::createHttpRequest(result);
      return request_type(std::get<0>(request), id, std::get<1>(request), std::get<2>(request));
	} else {
	  HelperRoutines::warning("Cannot lock mutex on a request storage.");
	}
    return request_type("",-1,"", 0);  // TODO(alex): exception?
  }

  bool requestAvailable() {
    bool available = false;
	if (pthread_mutex_lock(&results_mutex) == 0) {
      available = !results.empty();
      if (pthread_mutex_unlock(&results_mutex) != 0) {
        HelperRoutines::warning("Cannot unlock mutex on a request storage.");
      }
	} else {
	  HelperRoutines::warning("Cannot lock mutex on a request storage.");
	}
	return available;
  }

  std::string retrieveResponse(int id) {
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
