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
  explicit ServerWorkerParameters(std::shared_ptr<RequestStorage> store):
      storage(store), requestAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER),
      work(true), requestAvailabilityCondition() {
    std::cout << "Create ServerWorkerParameters" << std::endl;
    pthread_cond_init(&requestAvailabilityCondition, NULL);
  }

  virtual ~ServerWorkerParameters() {
    std::cout << "Destroy Server Worker Parameters" << std::endl;
    pthread_cond_destroy(&requestAvailabilityCondition);
  }

  RequestStorage* getStorage() const {
    std::cout << "Get request storage" << std::endl;
    return storage.get();
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

  bool getWork() const {
    return work;
  }

 private:
  bool work;
  const std::shared_ptr<RequestStorage> storage;
  pthread_mutex_t requestAvailabilityMutex;
  pthread_cond_t requestAvailabilityCondition;

  // prevent copy
  ServerWorkerParameters(const ServerWorkerParameters&) = delete;
  ServerWorkerParameters& operator=(const ServerWorkerParameters&) = delete;
};

class ServerThread {
 public:
  explicit ServerThread(std::shared_ptr<RequestStorage> store):
      storage(store.get()) {
    std::cout << "ServerThread ctor" << std::endl;
    parameters = new ServerWorkerParameters(store);
    int e = pthread_create(&thread, NULL, ServerThread::serverThreadRoutine, &parameters);
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
      std::cout << "Joined, deleting parameters" <<std::endl;
    } else {
      std::cout << "Thread was not created, just deleting parameters" << std::endl;
    }
    delete parameters;
    std::cout << "Deleted, leaving" << std::endl;
  }

  static void * serverThreadRoutine (void *);

 private:
  RequestStorage * storage;
  ServerWorkerParameters * parameters;
  pthread_t thread;
  bool threadFailed;
  static std::size_t buffer_size;

  static void writeRequest(const RequestStorage::queue_type &, const int, RequestStorage *);
  static int connection (const std::string &, const int);

  // prevent copy
  ServerThread(const ServerThread&) = delete;
  ServerThread& operator=(const ServerThread&) = delete;
};

class ServerAgent {
 public:
  ServerAgent(std::shared_ptr<ProxyConfiguration> conf,
      std::shared_ptr<RequestStorage> store):
        threads(conf->getOutPoolCount()), configuration(conf),
        storage(store) {
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
       std::unique_ptr<ServerThread> p(new ServerThread(storage));
       threads.push_back(std::move(p));
       std::cout << "Created a thread" << std::endl;
     }
  }

 private:
  std::shared_ptr<ProxyConfiguration> configuration;
  std::shared_ptr<RequestStorage> storage;
  std::vector<std::unique_ptr<ServerThread>> threads;

  // prevent copy
  ServerAgent(const ServerAgent&) = delete;
  ServerAgent& operator=(const ServerAgent&) = delete;
};

#endif  // SRC_PROXY_SERVERAGENT_H_
