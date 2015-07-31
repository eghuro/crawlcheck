// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_REQUESTSTORAGE_H_
#define SRC_PROXY_REQUESTSTORAGE_H_

#include <pthread.h>
#include <memory>
#include <string>
#include <sstream>
#include <deque>
#include <tuple>
#include <utility>
#include "./HttpParser.h"
#include "./HelperRoutines.h"

class RequestStorage {
 public:
  typedef std::tuple<std::string, int, std::string, std::size_t> request_type;

  RequestStorage() : results(), results_mutex(PTHREAD_MUTEX_INITIALIZER) {}
  virtual ~RequestStorage() {}

  void insertParserResult(const HttpParserResult & result, int id) {
    if (pthread_mutex_lock(&results_mutex) == 0) {
      results.push_back(queue_type(result, id));
      // TODO(alex): push DB
      // TODO(alex): distinguish reqests and resopnses
      if (pthread_mutex_unlock(&results_mutex) == 0) {
        HelperRoutines::warning("Cannot unlock mutex on a request storage.");
      }
    } else {
      HelperRoutines::warning("Cannot lock mutex on a request storage.");
    }
  }

  request_type retrieveRequest() {
    if (pthread_mutex_lock(&results_mutex) == 0) {
      auto result_bundle = results.front();
      results.pop_front();
      if (pthread_mutex_unlock(&results_mutex) != 0) {
        HelperRoutines::warning("Cannot unlock mutex on a request storage.");
      }

      int id = std::get<1>(result_bundle);
      auto result = std::get<0>(result_bundle);
      return request_type(result.getRaw(), id, result.getRequestUri(),
          result.getPort());
    } else {
      HelperRoutines::warning("Cannot lock mutex on a request storage.");
    }
    return request_type("", -1, "", 0);  // TODO(alex): exception?
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
  typedef std::pair<HttpParserResult, int> queue_type;
  std::deque<queue_type> results;
  pthread_mutex_t results_mutex;
};

#endif  // SRC_PROXY_REQUESTSTORAGE_H_
