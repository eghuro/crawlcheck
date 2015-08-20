// Copyright 2015 Alexandr Mansurov
#ifndef SRC_PROXY_SERVERAGENT_H_
#define SRC_PROXY_SERVERAGENT_H_

#include <pthread.h>
#include <memory>
#include <string>
#include <vector>
#include "RequestStorage.h"
#include "ProxyConfiguration.h"
#include "HelperRoutines.h"

class ServerWorkerParameters {
 public:
  //RequestStorage will not be deleted here
  explicit ServerWorkerParameters(RequestStorage * store, pthread_mutex_t * storeLock):
      storage(store), requestAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER),
      work(true), requestAvailabilityCondition(), storageLock(storeLock) {
    assert(store!=nullptr);
    assert(storage != nullptr);
    HelperRoutines::info("Create ServerWorkerParameters");
    int e = pthread_cond_init(&requestAvailabilityCondition, NULL);
    if (e != 0) HelperRoutines::warning("Initialize condition variable (request availability)", strerror(e));
  }

  virtual ~ServerWorkerParameters() {
    HelperRoutines::info("Destroy Server Worker Parameters");
    int e = pthread_cond_destroy(&requestAvailabilityCondition);
    if (e != 0) {
      HelperRoutines::warning("Destroy conditional variable (request availability)", strerror(e));
    }
  }

  RequestStorage* getStorage() {
    HelperRoutines::info("Get request storage");
    if (storage == nullptr) HelperRoutines::warning("Returning nullptr");
    return storage;
  }

  pthread_mutex_t* getStorageLock() {
    if (storageLock == nullptr) HelperRoutines::warning("Returning nullptr");
    return storageLock;
  }

  pthread_mutex_t * getRequestAvailabilityMutex() {
    return &requestAvailabilityMutex;
  }

  pthread_cond_t * getRequestAvailabilityCondition() {
    return &requestAvailabilityCondition;
  }

   void setWork(bool value) {
    work = value;
  }

  bool doWork() const {
    return work;
  }

 private:
  bool work;
  RequestStorage * storage;
  pthread_mutex_t * storageLock;
  pthread_mutex_t requestAvailabilityMutex;
  pthread_cond_t requestAvailabilityCondition;

  // prevent copy
  ServerWorkerParameters(const ServerWorkerParameters&) = delete;
  ServerWorkerParameters& operator=(const ServerWorkerParameters&) = delete;
};

class ServerThread {
 public:
  //RequestStorage will not be deleted here
  explicit ServerThread(RequestStorage * store, pthread_mutex_t * storeLock):
      storage(store), storageLock(storeLock) {
    HelperRoutines::info("ServerThread ctor");

    ServerWorkerParameters * parameters = new ServerWorkerParameters(store, storeLock);
    int e = pthread_create(&thread, NULL, ServerThread::serverThreadRoutine, parameters );
    if (e != 0) {
      threadFailed = true;
      HelperRoutines::error(strerror(e));
    } else {
      threadFailed = false;
      HelperRoutines::info("New server thread created");
    }
  }

  virtual ~ServerThread() {
    HelperRoutines::info("Destroying server thread");
    if (!threadFailed) {
      std::cout << "Join" << std::endl;
      int e = pthread_join(thread, NULL);
      if (e != 0) {
        HelperRoutines::warning("Pthread_join", strerror(e));
      } else {
        HelperRoutines::info("Join successful");
      }
    } else {
      HelperRoutines::info("Thread was not created");
    }

    HelperRoutines::info("Leaving");
  }

  static void * serverThreadRoutine (void *);

  /*void destroy() {
    pthread_cancel(thread);
  }*/
 private:
  RequestStorage * storage;
  pthread_mutex_t * storageLock;
  pthread_t thread;
  bool threadFailed;
  static std::size_t buffer_size;

  static void writeRequest(const RequestStorage::queue_type &, const int, RequestStorage *, pthread_mutex_t *);
  static int connection (const std::string &, const int);

  // prevent copy
  ServerThread(const ServerThread&) = delete;
  ServerThread& operator=(const ServerThread&) = delete;
};

class ServerAgent {
 public:
  //RequestStorage will not be deleted here
  ServerAgent(std::shared_ptr<ProxyConfiguration> conf,
      RequestStorage * store, pthread_mutex_t * storeLock):
        threads(conf->getOutPoolCount()), configuration(conf),
        storage(store), storageLock(storeLock) {
    HelperRoutines::info("Creating ServerAgent");
    std::ostringstream oss;
    oss << "Threads: "<<conf->getOutPoolCount();
    HelperRoutines::info(oss.str());
  }

  virtual ~ServerAgent() {
    HelperRoutines::info("Destroying ServerAgent");
  }

  void start() {
    HelperRoutines::info("Creating pool");
    // create pool
    for (int i = 0; i < configuration->getOutPoolCount(); i++) {
       std::unique_ptr<ServerThread> p(new ServerThread(storage, storageLock));
       threads.push_back(std::move(p));
       HelperRoutines::info("Created a thread");
     }
  }

  /*void stop() {
    for (auto it = threads.begin(); it != threads.end(); ++it) {
      (*it)->destroy();
    }
  }*/

 private:
  std::shared_ptr<ProxyConfiguration> configuration;
  RequestStorage * storage;
  pthread_mutex_t * storageLock;
  std::vector<std::unique_ptr<ServerThread>> threads;

  // prevent copy
  ServerAgent(const ServerAgent&) = delete;
  ServerAgent& operator=(const ServerAgent&) = delete;
};

#endif  // SRC_PROXY_SERVERAGENT_H_
