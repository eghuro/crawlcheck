// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_PROXYWORKER_H_
#define SRC_PROXY_PROXYWORKER_H_

#include <string.h>
#include <assert.h>
#include <pthread.h>
#include <err.h>
#include "./HelperRoutines.h"

class ProxyWorker {
 public:
  ProxyWorker() : thread(0) {}
  virtual ~ProxyWorker() {}

  void startThread(int fd) {
    assert(sizeof (void *) >= sizeof (int));
    void * parameter = reinterpret_cast<void *>(fd);
    int e = pthread_create(&thread, NULL, threadRoutine, parameter);
    if (e != 0) {
      errx(1, "pthread_create: %s", strerror(e));
    }
  }

 private:
  pthread_t thread;

  static void* threadRoutine(void * arg);
};
#endif  // SRC_PROXY_PROXYWORKER_H_
