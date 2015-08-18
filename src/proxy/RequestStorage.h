// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_REQUESTSTORAGE_H_
#define SRC_PROXY_REQUESTSTORAGE_H_

#include <pthread.h>
#include <string.h>
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

  RequestStorage(std::shared_ptr<Database> db) :
      database(db), responseSubscribers(), requestSubscribers(),
      database_mutex(PTHREAD_MUTEX_INITIALIZER) {}
  virtual ~RequestStorage() {
    int e = pthread_mutex_unlock(&database_mutex);
    if (e != 0) {
      HelperRoutines::warning(unlock, strerror(e));
    }
  }

  bool responseAvailable(std::size_t trid) {
    bool available = false;
    int e0 = pthread_mutex_lock(&database_mutex);
    if (e0 == 0) {
      available = database->isResponseAvailable(trid);

      int e1 = pthread_mutex_unlock(&database_mutex);
      if (e1 != 0) {
        HelperRoutines::warning(unlock, strerror(e1));
      }
    } else {
      HelperRoutines::warning(lock, strerror(e0));
    }
    return available;
  }

  std::size_t insertRequest(const HttpParserResult & result) {
    if (result.isRequest()) {
      std::size_t id;
      int e0 = pthread_mutex_lock(&database_mutex);
      if (e0 == 0) {
        id = database->setClientRequest(result);

        int e1 = pthread_mutex_unlock(&database_mutex);
        if (e1 != 0) {
          HelperRoutines::warning(unlock, strerror(e1));
        }

        for (auto it = requestSubscribers.begin();
            it != requestSubscribers.end();
            it++) {
          int e2 = pthread_mutex_lock(it->mutex);
          if (e2 == 0) {
            int e3 = pthread_cond_broadcast(it->cond);
            if (e3 != 0) {
              HelperRoutines::warning("Cannot notify workers", strerror(e3));
            }
            int e4 = pthread_mutex_unlock(it->mutex);
            if (e4 != 0) {
              HelperRoutines::warning("Cannot unlock mutex for notify on request insertion", strerror(e4));
            }
          } else {
            HelperRoutines::warning("Cannot lock mutex for notify on request insertion", strerror(e2));
          }
        }
      } else {
        HelperRoutines::warning(lock, strerror(e0));
      }

      return id;
    }

    return 0;
  }

  void insertResponse(const HttpParserResult & result, std::size_t transactionId) {
    if (result.isResponse()) {
      int e0 = pthread_mutex_lock(&database_mutex);
      if (e0 == 0) {
        database->setServerResponse(transactionId, result);

        int e1 = pthread_mutex_unlock(&database_mutex);
        if (e1 != 0) {
          HelperRoutines::warning(unlock, strerror(e1));
        }

        for (auto it = responseSubscribers.find(transactionId);
            it != responseSubscribers.end();
            ++it) {

          int e2 = pthread_mutex_lock(it->second.first);
          if (e2 == 0) {
            int e3 = pthread_cond_broadcast(it->second.second);
            if (e3 != 0) {
              HelperRoutines::warning("Cannot notify workers", strerror(e3));
            }
            int e4 = pthread_mutex_unlock(it->second.first);
            if (e4 != 0) {
              HelperRoutines::warning("Cannot unlock mutex for notify on request insertion", strerror(e4));
            }
          } else {
            HelperRoutines::warning("Cannot lock mutex for notify on request insertion", strerror(e2));
          }
        }

      } else {
        HelperRoutines::warning(lock, strerror(e0));
      }
    }
  }

  /**
   * Retrieve a new request from the storage and then remove it from there.
   * @return HttpParser result and it's transaction identifier
   */
  queue_type retrieveRequest() {
    int e0 = pthread_mutex_lock(&database_mutex);
    queue_type cr = queue_type(HttpParserResult(), -1);
    if (e0 == 0) {
      auto cr_ = database->getClientRequest();

      int e1 = pthread_mutex_unlock(&database_mutex);
      if (e1 != 0) {
        HelperRoutines::warning(unlock, strerror(e1));
      }

      return cr_;
    } else {
      HelperRoutines::warning(lock, strerror(e0));
    }
    return cr;
  }

  /**
   * Is there a new request in the storage?
   * @return the request storage is not empty
   */
  bool requestAvailable() {
    bool available = false;
    int e0 = pthread_mutex_lock(&database_mutex);
    if (e0 == 0) {
      available = database->isRequestAvailable();

      int e1 = pthread_mutex_unlock(&database_mutex);
      if (e1 != 0) {
        HelperRoutines::warning(unlock, strerror(e1));
      }
    } else {
      HelperRoutines::warning(lock, strerror(e0));
    }

    return available;
  }


  /**
   * Retrieve a response from the response storage
   * @param id transaction id
   * @return raw HTTP Response message
   */
  std::string retrieveResponse(std::size_t id) {
    int e0 = pthread_mutex_lock(&database_mutex);
    if (e0 == 0) {
      auto response = database->getServerResponse(id);

      int e1 = pthread_mutex_unlock(&database_mutex);
      if (e1 != 0) {
        HelperRoutines::warning(unlock, strerror(e1));
      }

      if (response.isResponse()) {
        return response.getRaw();
      }
    }  else {
      HelperRoutines::warning(unlock, strerror(e0));
    }
    return "";  // TODO(alex): exception?
  }

  void subscribeWait4Response(const int transactionId, pthread_mutex_t * mutex, pthread_cond_t * cond) {
    responseSubscribers.insert(
        std::pair<int, std::pair<pthread_mutex_t *, pthread_cond_t *>>(
            transactionId, std::pair<pthread_mutex_t *, pthread_cond_t *>(mutex, cond)));
  }

  void subscribeWait4Request(pthread_mutex_t * mutex, pthread_cond_t * cond) {
    std::cout << "Subscribe: wait for request" << std::endl;

    my_pair pair;
    pair.mutex = mutex;
    pair.cond = cond;

    requestSubscribers.push_back(std::move(pair));
    std::cout << "Subscribed" << std::endl;
  }
 private:
  struct my_pair {
    pthread_mutex_t * mutex;
    pthread_cond_t * cond;
  };
  pthread_mutex_t database_mutex;
  std::shared_ptr<Database> database;
  std::multimap<int, const std::pair<pthread_mutex_t *, pthread_cond_t *>> responseSubscribers;
  std::deque<my_pair> requestSubscribers;

  static const std::string lock;
  static const std::string unlock;
};

#endif  // SRC_PROXY_REQUESTSTORAGE_H_
