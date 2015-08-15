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
#include "./db.h"

// TODO(alex): rename
/**
 * Storage for requests and responses
 */
class RequestStorage {
 public:
  typedef std::pair<HttpParserResult, std::size_t> queue_type;
  typedef std::pair<std::size_t, HttpParserResult> map_type;

  RequestStorage(std::shared_ptr<Database> db) : requests(), responses(),
      requests_mutex(PTHREAD_MUTEX_INITIALIZER),
      responses_mutex(PTHREAD_MUTEX_INITIALIZER),
      database(db), responseSubscribers(), requestSubscribers(){}
  virtual ~RequestStorage() {
    pthread_mutex_unlock(&requests_mutex);
    pthread_mutex_unlock(&responses_mutex);
  }

  bool responseAvailable(std::size_t trid) {
    int e;
    bool available = false;
    if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
      available = database->isResponseAvailable(trid);
      if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
        HelperRoutines::warning(unlock_request, strerror(e));
      }
    } else {
      HelperRoutines::warning(lock_request, strerror(e));
    }
    return available;
  }

  std::size_t insertRequest(const HttpParserResult & result) {
    if (result.isRequest()) {
      int e;
      if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {

        auto id = database->setClientRequest(result);

        for (auto it = requestSubscribers.begin();
            it != requestSubscribers.end();
            it++) {
          pthread_mutex_lock(it->first);
          pthread_cond_broadcast(it->second);
          pthread_mutex_unlock(it->first);
        }

        if ((e = pthread_mutex_unlock(&requests_mutex)) != 0) {
          HelperRoutines::warning(unlock_request, strerror(e));
        }

        return id;
      } else {
        HelperRoutines::warning(lock_request, strerror(e));
      }
    }
    return 0;
  }

  void insertResponse(const HttpParserResult & result, std::size_t transactionId) {
    if (result.isResponse()) {
      int e;
      if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
        database->setServerResponse(transactionId, result);

        for (auto it = responseSubscribers.find(transactionId);
            it != responseSubscribers.end();
            ++it) {
          pthread_mutex_lock(it->second.first);
          pthread_cond_broadcast(it->second.second);
          pthread_mutex_unlock(it->second.first);
        }

        if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
          HelperRoutines::warning(unlock_request, strerror(e));
        }
      } else {
        HelperRoutines::warning(lock_request, strerror(e));
      }
    }
  }

  /**
   * Retrieve a new request from the storage and then remove it from there.
   * @return HttpParser result and it's transaction identifier
   */
  queue_type retrieveRequest() {
    int e;
    if ((e = pthread_mutex_lock(&requests_mutex)) == 0) {
      auto result_bundle = database->getClientRequest();
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
      available = database->isRequestAvailable();
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
  std::string retrieveResponse(std::size_t id) {
    int e;
    if ((e = pthread_mutex_lock(&responses_mutex)) == 0) {
      auto response = database->getServerResponse(id);
      if (response.isResponse()) {
        return response.getRaw();
      }
      if ((e = pthread_mutex_unlock(&responses_mutex)) != 0) {
        HelperRoutines::warning(unlock_response, strerror(e));
      }
    } else {
      HelperRoutines::warning(lock_response, strerror(e));
    }

    return "";  // TODO(alex): exception?
  }

  void subscribeWait4Response(const int transactionId, pthread_mutex_t * mutex, pthread_cond_t * cond) {
    responseSubscribers.insert(
        std::pair<int, std::pair<pthread_mutex_t *, pthread_cond_t *>>(
            transactionId, std::pair<pthread_mutex_t *, pthread_cond_t *>(mutex, cond)));
  }

  void subscribeWait4Request(pthread_mutex_t * mutex, pthread_cond_t * cond) {
    requestSubscribers.push_back(std::pair<pthread_mutex_t *, pthread_cond_t *>(mutex, cond));
  }
 private:
  std::deque<queue_type> requests;
  std::map<int, HttpParserResult> responses;
  pthread_mutex_t requests_mutex, responses_mutex;
  std::shared_ptr<Database> database;
  std::multimap<int, const std::pair<pthread_mutex_t *, pthread_cond_t *>> responseSubscribers;
  std::deque<std::pair<pthread_mutex_t *, pthread_cond_t *>> requestSubscribers;

  static const std::string lock_response;
  static const std::string unlock_response;
  static const std::string lock_request;
  static const std::string unlock_request;
};

#endif  // SRC_PROXY_REQUESTSTORAGE_H_
