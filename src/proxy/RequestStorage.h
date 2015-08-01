// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_REQUESTSTORAGE_H_
#define SRC_PROXY_REQUESTSTORAGE_H_

#include <pthread.h>
#include <err.h>
#include <memory>
#include <string>
#include <sstream>
#include <deque>
#include <tuple>
#include <utility>
#include <cassert>
#include "./HttpParser.h"
#include "./HelperRoutines.h"

// TODO(alex): rename
// TODO(alex): refactoring!! - request vs response?
class RequestStorage {
 public:
  typedef std::pair<HttpParserResult, int> queue_type;

  RequestStorage() : requests(), responses(),
      requests_mutex(PTHREAD_MUTEX_INITIALIZER),
      responses_mutex(PTHREAD_MUTEX_INITIALIZER) {}
  virtual ~RequestStorage() {}

  void insertParserResult(const HttpParserResult & result, int id) {
    // TODO(alex): push DB
    // TODO(alex): response goes to checker

    int e;
    if (result.isRequest()) {
      if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
        requests.push_back(queue_type(result, id));

        if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
          HelperRoutines::warning("Cannot unlock mutex on a request storage.", strerror(e));
        }
      } else {
        HelperRoutines::warning("Cannot lock mutex on a request storage.");
      }
    } else if (result.isResponse()) {
      if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
        responses.push_back(queue_type(result, id));

        if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
          HelperRoutines::warning("Cannot unlock mutex on a response storage.", strerror(e));
        }
      } else {
        HelperRoutines::warning("Cannot lock mutex on a response storage.");
      }
    } else {
      assert(false);
    }

  }

  queue_type retrieveRequest() {
    int e;
    if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
      auto result_bundle = requests.front();
      requests.pop_front();
      if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
        HelperRoutines::warning("Cannot unlock mutex on a request storage.", strerror(e));
      }
      return result_bundle;
    } else {
      HelperRoutines::warning("Cannot lock mutex on a request storage.", strerror(e));
    }
    return queue_type(HttpParserResult(),-1);  // TODO(alex): exception?
  }

  bool requestAvailable() {
    bool available = false;
    int e;
    if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
      available = !requests.empty();
      if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
        HelperRoutines::warning("Cannot unlock mutex on a request storage.", strerror(e));
      }
    } else {
      HelperRoutines::warning("Cannot lock mutex on a request storage.", strerror(e));
    }
    return available;
  }

  std::string retrieveResponse(int id) {
    int e;
    if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
      auto result_bundle = responses.front();
      responses.pop_front();
      if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
        HelperRoutines::warning("Cannot unlock mutex on a response storage.", strerror(e));
      }
      return std::get<0>(result_bundle).getRaw();
    } else {
      HelperRoutines::warning("Cannot lock mutex on a response storage.", strerror(e));
    }
    return "";  // TODO(alex): exception?
  }

  bool responseAvailable() {
    bool available = false;
    int e;
    if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
      available = !responses.empty();
      if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
        HelperRoutines::warning("Cannot unlock mutex on a response storage.", strerror(e));
      }
    } else {
      HelperRoutines::warning("Cannot lock mutex on a response storage.", strerror(e));
    }
    return available;
  }

  bool done() {
    return false;
  }

 private:
  std::deque<queue_type> requests, responses;
  pthread_mutex_t requests_mutex, responses_mutex;
};

#endif  // SRC_PROXY_REQUESTSTORAGE_H_
