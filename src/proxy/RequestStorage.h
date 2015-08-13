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
#include <map>
#include <utility>
#include <cassert>
#include "./HttpParser.h"
#include "./HelperRoutines.h"
#include "../db/db.h"

// TODO(alex): rename
// TODO(alex): refactoring!! - request vs response?, template method?
/**
 * Storage for requests and responses
 */
class RequestStorage {
 public:
  typedef std::pair<HttpParserResult, int> queue_type;
  typedef std::pair<int, HttpParserResult> map_type;

  RequestStorage(std::shared_ptr<Database> db) : requests(), responses(),
      requests_mutex(PTHREAD_MUTEX_INITIALIZER),
      responses_mutex(PTHREAD_MUTEX_INITIALIZER),
      database(db){}
  virtual ~RequestStorage() {
    pthread_mutex_unlock(&requests_mutex);
    pthread_mutex_unlock(&responses_mutex);
  }

  /**
   * Insert HttpParseerResult into storage, pushes DB
   * @param result parsed communication HttpParserResult of type request or response
   * @param id transaction identifier
   */
  void insertParserResult(const HttpParserResult & result, int id) {
    int e;
    if (result.isRequest()) {
      database->setClientRequest(result);

      if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
        requests.push_back(queue_type(result, id));

        if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
          HelperRoutines::warning(unlock_request, strerror(e));
        }
      } else {
        HelperRoutines::warning(lock_request, strerror(e));
      }
    } else if (result.isResponse()) {
      database->setServerResponse(result);

      if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
        responses.insert(map_type(id, result));

        if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
          HelperRoutines::warning(unlock_request, strerror(e));
        }
      } else {
        HelperRoutines::warning(lock_request, strerror(e));
      }
    } else {
      assert(false);
    }
  }

  /**
   * Retrieve a new request from the storage and then remove it from there.
   * @return HttpParser result and it's transaction identifier
   */
  queue_type retrieveRequest() {
    int e;
    if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
      auto result_bundle = requests.front();
      requests.pop_front();
      if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
        HelperRoutines::warning(unlock_request, strerror(e));
      }
      return result_bundle;
    } else {
      HelperRoutines::warning(lock_request, strerror(e));
    }
    return queue_type(HttpParserResult(), -1);  // TODO(alex): exception?
  }

  /**
   * Is there a new request in the storage?
   * @return the request storage is not empty
   */
  bool requestAvailable() {
    bool available = false;
    int e;
    if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
      available = !requests.empty();
      if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
        HelperRoutines::warning(unlock_request, strerror(e));
      }
    } else {
      HelperRoutines::warning(lock_request, strerror(e));
    }
    return available;
  }

  /**
   * Retrieve a response from the response storage
   * @param id transaction id
   * @return raw HTTP Response message
   */
  std::string retrieveResponse(int id) {
    int e;
    bool ok = false;
    if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
      auto result_bundle = responses.find(id);
      if (result_bundle != responses.end()) {
        responses.erase(result_bundle);
        ok = true;
      }
      if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
        HelperRoutines::warning(unlock_response, strerror(e));
      }
      if (ok) {
        return std::get<1>(*result_bundle).getRaw();
      }
    } else {
      HelperRoutines::warning(lock_response, strerror(e));
    }

    return "";  // TODO(alex): exception?
  }

  /**
   * Is there a response available?
   * @param the ressponse storage is not empty
   */
  bool responseAvailable() {
    bool available = false;
    int e;
    if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
      available = !responses.empty();
      if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
        HelperRoutines::warning(unlock_response, strerror(e));
      }
    } else {
      HelperRoutines::warning(lock_response, strerror(e));
    }
    return available;
  }

  // TODO(alex): implement RequestStorage done
  bool done() {
    return false;
  }

 private:
  std::deque<queue_type> requests;
  std::map<int, HttpParserResult> responses;
  pthread_mutex_t requests_mutex, responses_mutex;
  std::shared_ptr<Database> database;

  static const std::string lock_response;
  static const std::string unlock_response;
  static const std::string lock_request;
  static const std::string unlock_request;
};

#endif  // SRC_PROXY_REQUESTSTORAGE_H_
