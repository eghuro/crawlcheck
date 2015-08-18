// Copyright 2015 Alexandr Mansurov
#ifndef SRC_PROXY_SERVERAGENT_H_
#define SRC_PROXY_SERVERAGENT_H_

#include <pthread.h>
#include <memory>
#include <string>
#include <vector>
#include "RequestStorage.h"
#include "ProxyConfiguration.h"

class ServerWorkerParameters {
 public:
  //RequestStorage will not be deleted here
  explicit ServerWorkerParameters(RequestStorage * store, pthread_mutex_t * storeLock):
      storage(store), requestAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER),
      work(true), requestAvailabilityCondition(), storageLock(storeLock) {
    assert(store!=nullptr);
    assert(storage != nullptr);
    std::cout << "Create ServerWorkerParameters" << std::endl;
    pthread_cond_init(&requestAvailabilityCondition, NULL);
  }

  virtual ~ServerWorkerParameters() {
    std::cout << "Destroy Server Worker Parameters" << std::endl;
    pthread_cond_destroy(&requestAvailabilityCondition);
  }

  RequestStorage* getStorage() {
    std::cout << "Get request storage" << std::endl;
    if (storage == nullptr) std::cout << "Returning nullptr";
    return storage;
  }

  pthread_mutex_t* getStorageLock() {
    if (storageLock == nullptr) std::cout << "Returning nullptr";
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
    std::cout << "ServerThread ctor" << std::endl;

    ServerWorkerParameters * parameters = new ServerWorkerParameters(store, storeLock);
    int e = pthread_create(&thread, NULL, ServerThread::serverThreadRoutine, parameters );
    if (e != 0) {
      threadFailed = true;
      HelperRoutines::error(strerror(e));
    } else {
      threadFailed = false;
      std::cout << "new thread created" << std::endl;
    }
  }

  virtual ~ServerThread() {
    std::cout << "Destroying server thread"<<std::endl;
    if (!threadFailed) {
      std::cout << "Join" << std::endl;
      int e = pthread_join(thread, NULL);
      if (e != 0) {
        HelperRoutines::warning("Pthread_join", strerror(e));
      } else {
        std::cout << "Join successful" << std::endl;
      }
    } else {
      std::cout << "Thread was not created" << std::endl;
    }

    std::cout << "Leaving" << std::endl;
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
    std::cout << "Creating ServerAgent" << std::endl;
    std::cout << "Threads: "<<conf->getOutPoolCount() << std::endl;
  }

  virtual ~ServerAgent() {
    std::cout << "Destroying ServerAgent" << std::endl;
  }

  void start() {
    std::cout << "Creating pool" << std::endl;
    // create pool
    for (int i = 0; i < configuration->getOutPoolCount(); i++) {
       std::unique_ptr<ServerThread> p(new ServerThread(storage, storageLock));
       threads.push_back(std::move(p));
       std::cout << "Created a thread" << std::endl;
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
