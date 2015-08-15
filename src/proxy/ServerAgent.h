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
      storage(store), requestAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER) {
    pthread_cond_init(&requestAvailabilityCondition, NULL);
  }

  virtual ~ServerWorkerParameters() {
    pthread_cond_destroy(&requestAvailabilityCondition);
  }

  std::shared_ptr<RequestStorage> getStorage() const {
    return store;
  }

  pthread_mutex_t * getRequestAvailabilityMutex() const {
    return &requestAvailabilityMutex;
  }
  pthread_cond_t * getRequestAvailabilityCondition() const {
    return &requestAvailabilityCondition;
  }

 private:
  const std::shared_ptr<RequestStorage> store;
  const pthread_mutex_t requestAvailabilityMutex;
  const pthread_cond_t requestAvailabilityCondition;
};

class ServerThread {
 public:
  explicit ServerThread(std::shared_ptr<RequestStorage> store):
      storage(store) {
    parameters = new ServerWorkerParameters(store);
    pthread_create(&thread, NULL, ServerThread::serverThreadRoutine, &parameters);
  }
  virtual ~ServerThread() {
    pthread_join(thread, NULL);
    delete parameters;
  }

  static void * serverThreadRoutine (void *);

 private:
  std::shared_ptr<RequestStorage> storage;
  ServerWorkerParameters * parameters;
  pthread_t thread;
  static std::size_t buffer_size;

  static void writeRequest(const RequestStorage::queue_type &, const int, std::shared_ptr<RequestStorage>);
  static int connection (const std::string &, const int);

  // prevent copy
  ServerAgent(const ServerAgent&) = delete;
  ServerAgent& operator=(const ServerAgent&) = delete;
};

class ServerAgent {
 public:
  ServerAgent(std::shared_ptr<ProxyConfiguration> conf,
      std::shared_ptr<RequestStorage> store):
        threads(conf->getOutPoolCount()), configuration(conf),
        storage(store) {}
  virtual ~ServerAgent() {}

  void start() {
    // create pool
    for (int i = 0; i < configuration->getOutPoolCount(); i++) {
       std::unique_ptr<ServerThread> p(new ServerThread(storage));
       threads.push_back(std::move(p));
     }
  }

 private:
  std::shared_ptr<ProxyConfiguration> configuration;
  std::shared_ptr<RequestStorage> storage;
  std::vector<ServerThread> threads;

  // prevent copy
   ServerAgent(const ServerAgent&) = delete;
   ServerAgent& operator=(const ServerAgent&) = delete;
};

#endif  // SRC_PROXY_SERVERAGENT_H_
