// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_PROXYWORKER_H_
#define SRC_PROXY_PROXYWORKER_H_

#include <memory>
#include <string.h>
#include <assert.h>
#include <pthread.h>
#include <err.h>
#include "./HelperRoutines.h"
#include "./RequestStorage.h"

class ProxyWorker {
 public:
  // TODO(alex):make singleton!
  ProxyWorker() : client_thread(0), server_thread(0) {}
  virtual ~ProxyWorker();

  void startThread(int fd);

  
 private:
  pthread_t client_thread, server_thread;
  std::shared_ptr<RequestStorage> request_storage = std::unique_ptr<RequestStorage>(new RequestStorage());

  static const int buffer_size;

  static void* clientThreadRoutine(void * arg);
  static void* serverThreadRoutine(void * arg);
  static void handleClientRequest(int new_fd,
    std::shared_ptr<RequestStorage> storage);
  static void handleClientResponse(int new_fd,
    std::shared_ptr<RequestStorage> storage);

  void createThreads(void* parameter);
};
#endif  // SRC_PROXY_PROXYWORKER_H_
