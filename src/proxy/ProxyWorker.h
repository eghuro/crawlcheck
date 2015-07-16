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
  virtual ~ProxyWorker() {
    void *retval_client, *retval_server;

    // zrusit client thread
    int e = pthread_join(client_thread, &retval_client);
    if (e != 0) {
    	errx(1, "pthread_join (client): %s", strerror (e));
    }

    // zrusit server thread
    e = pthread_join(server_thread, &retval_server);
    if (e != 0) {
      errx(1, "pthread_join (client): %s", strerror (e));
    }
  }

  void startThread(int fd) {
    assert(sizeof (void *) >= sizeof (int));
    void * parameter = reinterpret_cast<void *>(fd);

    // vytvorit client thread
    int e = pthread_create(&client_thread, NULL, clientThreadRoutine, parameter);
    if (e != 0) {
      errx(1, "pthread_create (client): %s", strerror(e));
    } else {
    	// povedlo se
    	// vytvorit server thread
    	e = pthread_create(&server_thread, NULL, serverThreadRoutine, parameter);
        if (e != 0) {
          // nepovedlo se
          errx(1, "pthread_create (server): %s", strerror(e));
          // zrusit client thread
          void *retval_client;
          e = pthread_join(client_thread, &retval_client);
          if (e != 0) {
          	errx(1, "pthread_join (client): %s", strerror (e));
          }
        }
    }
  }

  static std::unique_ptr<RequestStorage> request_storage;
 private:
  pthread_t client_thread, server_thread;

  static const int buffer_size;

  static void* clientThreadRoutine(void * arg);
  static void* serverThreadRoutine(void * arg);
};
#endif  // SRC_PROXY_PROXYWORKER_H_
