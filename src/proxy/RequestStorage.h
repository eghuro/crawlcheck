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
#include "./ThreadedHelperRoutines.h"
#include "./db.h"

// TODO(alex): rename
/**
 * Storage for requests and responses
 */
class RequestStorage {
 public:
  typedef std::pair<HttpParserResult, std::size_t> queue_type;
  typedef std::pair<std::size_t, HttpParserResult> map_type;

  explicit RequestStorage(DatabaseConfiguration conf, std::size_t serverPoolCount = 0) :
      responseSubscribers(), subscribed(0), maxSubscribers(serverPoolCount), configuration(conf) {
    HelperRoutines::info("New RequestStorage");
    reqSubscribers = new my_pair[serverPoolCount];
  }
  virtual ~RequestStorage() {
    HelperRoutines::info("Delete RequestStorage");
    delete [] reqSubscribers;
  }

  bool responseAvailable(std::size_t trid) {
    //HelperRoutines::info("RS responseAvailable");
    try {
      Database database(configuration);
      return database.isResponseAvailable(trid);
    } catch (const sql::SQLException & ex) {
      HelperRoutines::warning(ex.what());
    } catch (...) {
      HelperRoutines::error("Database exception");
    }
  }

  std::size_t insertRequest(const HttpParserResult & result) {
    HelperRoutines::info("RS insert request");
    std::size_t id;
    if (result.isRequest()) {
      try {
        Database database(configuration);
        id = database.setClientRequest(result);
      } catch (const sql::SQLException & ex) {
        HelperRoutines::warning(ex.what());
      } catch (...) {
        HelperRoutines::error("Database exception");
      }

      notifyRequest();

      return id;
    }

    return 0;
  }

  void insertResponse(const HttpParserResult & result, std::size_t transactionId) {
    HelperRoutines::info("RS insertResponse");
    if (result.isResponse()) {
      try {
        Database database(configuration);
        database.setServerResponse(transactionId, result);
      } catch (const sql::SQLException & ex) {
        HelperRoutines::warning(ex.what());
      } catch (...) {
        HelperRoutines::error("Database exception");
      }

      notifyResponse(transactionId);
    }
  }

  /**
   * Retrieve a new request from the storage and then remove it from there.
   * @return HttpParser result and it's transaction identifier
   */
  queue_type retrieveRequest() {
    HelperRoutines::info("RS retrieveRequest");

    try {
      Database database(configuration);
      return database.getClientRequest();
    } catch (const sql::SQLException & ex) {
      HelperRoutines::warning(ex.what());
    } catch (...) {
      HelperRoutines::error("Database exception");
    }
  }

  /**
   * Is there a new request in the storage?
   * @return the request storage is not empty
   */
  bool requestAvailable() {
   // HelperRoutines::info("RS request available");

    bool available = false;

    try {
      Database database(configuration);
      available = database.isRequestAvailable();
    } catch (const sql::SQLException & ex) {
      HelperRoutines::warning(ex.what());
    } catch (...) {
      HelperRoutines::error("Database exception");
    }

    //HelperRoutines::info(HelperRoutines::to_string(available));

    return available;
  }


  /**
   * Retrieve a response from the response storage
   * @param id transaction id
   * @return raw HTTP Response message
   */
  std::string retrieveResponse(std::size_t id) {
    HelperRoutines::info("RS response available");

    try {
      Database database(configuration);
      auto response = database.getServerResponse(id);

      if (response.isResponse()) {
        return response.getRaw();
      }
    } catch (const sql::SQLException & ex) {
      HelperRoutines::warning(ex.what());
    } catch (...) {
      HelperRoutines::error("Database exception");
    }

    return "";  // TODO(alex): exception?
  }

  void subscribeWait4Response(const int transactionId, pthread_mutex_t * mutex, pthread_cond_t * cond) {
    HelperRoutines::info("Subscribe - wait for response");
    responseSubscribers.insert(
        std::pair<int, std::pair<pthread_mutex_t *, pthread_cond_t *>>(
            transactionId, std::pair<pthread_mutex_t *, pthread_cond_t *>(mutex, cond)));
  }

  void subscribeWait4Request(pthread_mutex_t * mutex, pthread_cond_t * cond) {
    HelperRoutines::info("Subscribe - wait for request");

    if (subscribed < maxSubscribers) {
      reqSubscribers[subscribed].mutex = mutex;
      reqSubscribers[subscribed].cond = cond;
      subscribed++;
    }
  }

  void notifyRequest() {
    for(int i = 0; i < subscribed; i++) {
      ThreadedHelperRoutines::lock(reqSubscribers[i].mutex, "Notify on request insertion");
      int e3 = pthread_cond_broadcast(reqSubscribers[i].cond);
      if (e3 != 0) {
        HelperRoutines::warning("Cannot notify workers", strerror(e3));
      }
      ThreadedHelperRoutines::unlock(reqSubscribers[i].mutex, "Notify on request insertion");
    }
  }

  void notifyResponse(std::size_t transactionId) {
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
  }

 private:
  struct my_pair {
    pthread_mutex_t * mutex;
    pthread_cond_t * cond;
  };
  my_pair * reqSubscribers;
  std::size_t subscribed;
  const std::size_t maxSubscribers;

  DatabaseConfiguration configuration;
  std::multimap<int, const std::pair<pthread_mutex_t *, pthread_cond_t *>> responseSubscribers;

  // prevent copy
  RequestStorage(const RequestStorage&) = delete;
  RequestStorage& operator=(const RequestStorage&) = delete;

  static const std::string lock;
  static const std::string unlock;
};

#endif  // SRC_PROXY_REQUESTSTORAGE_H_
