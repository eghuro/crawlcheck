// Copyright 2015 Alexandr Mansurov
#ifndef SRC_PROXY_CLIENTAGENT_H_
#define SRC_PROXY_CLIENTAGENT_H_

#include <sys/types.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <netdb.h>
#include <unistd.h>
#include <pthread.h>
#include <memory>
#include <vector>
#include <cassert>
#include "db.h"
#include "RequestStorage.h"
#include "HelperRoutines.h"
#include "ProxyConfiguration.h"

/**
 * ClientWorkerParameters is a container for data needed inside a thread.
 *
 * It's not intended to be shared among threads (not thread-safe), instead
 * each ClientThread instance is supposed to create their own instance and
 * pass it to the underlying thread.
 */
class ClientWorkerParameters {
 public:
  explicit ClientWorkerParameters(std::shared_ptr<RequestStorage> stor):
    socket(-1), storage(stor), work(true),
    connectionAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER),
    responseAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER)  {
    pthread_cond_init(&connectionAvailabilityCondition, NULL);
    pthread_cond_init(&responseAvailabilityCondition, NULL);
  }
  virtual ~ClientWorkerParameters() {
    pthread_cond_destroy(&responseAvailabilityCondition);
    pthread_cond_destroy(&connectionAvailabilityCondition);
  }

  pthread_mutex_t * getConnectionAvailabilityMutex() {
    return &connectionAvailabilityMutex;
  }

  bool connectionAvailable() const {
    return socket >= 0;
  }

  pthread_cond_t * getConnectionAvailabilityCondition() {
    return &connectionAvailabilityCondition;
  }

  int getConnection() const {
    return socket;
  }

  void setConnection(const int fd) {
    socket = fd;
  }

  pthread_mutex_t * getResponseAvailabilityMutex() {
    return &responseAvailabilityMutex;
  }

  pthread_cond_t * getResponseAvailabilityCondition() {
    return &responseAvailabilityCondition;
  }

  std::shared_ptr<RequestStorage> getStorage() const {
    return storage;
  }

  void setWork(bool value) {
    work = value;
  }

  bool doWork() const {
    return work;
  }

 private:
  int socket;
  bool work;
  pthread_mutex_t connectionAvailabilityMutex, responseAvailabilityMutex, workMutex;
  pthread_cond_t connectionAvailabilityCondition, responseAvailabilityCondition;
  std::shared_ptr<RequestStorage> storage;

  // prevent copy
  ClientWorkerParameters(const ClientWorkerParameters&) = delete;
  ClientWorkerParameters& operator=(const ClientWorkerParameters&) = delete;
};

class ClientThread {
 public:
  explicit ClientThread(std::shared_ptr<RequestStorage> storage) {
    parameters = new ClientWorkerParameters(storage);
    pthread_create(&thread, NULL, ClientThread::clientThreadRoutine, &parameters);
  }

  virtual ~ClientThread() {
    pthread_join(thread, NULL);
    delete parameters;
  }

  void setSocket(const int socket) {
    //called from ClientAgent (main thread)
    //therefore lock needed
    pthread_mutex_lock(parameters->getConnectionAvailabilityMutex());
    parameters->setConnection(socket);
    pthread_cond_broadcast(parameters->getConnectionAvailabilityCondition());
    pthread_mutex_unlock(parameters->getConnectionAvailabilityMutex());
  }

  static void * clientThreadRoutine(void * arg);

 private:
  pthread_t thread;
  ClientWorkerParameters * parameters;
  static std::size_t buffer_size;

  // prevent copy
  ClientThread(const ClientThread&) = delete;
  ClientThread& operator=(const ClientThread&) = delete;

  static int establishConnection(ClientWorkerParameters * parameters);
  static std::vector<std::size_t> request(const ClientWorkerParameters *, int);
  static void response(const std::vector<std::size_t> &, const int, ClientWorkerParameters *);
};

class ClientAgent {
 public:
  ClientAgent(const std::shared_ptr<ProxyConfiguration> conf,
      std::shared_ptr<RequestStorage> store) :
    configuration(conf), storage(store), socketFd(-1),
    threads(conf->getInPoolCount()) {}

  virtual ~ClientAgent() {
    close(socketFd);
  }

  void start() {
    createPool();
    doListen();
  }
 private:
  const std::shared_ptr<ProxyConfiguration> configuration;
  const std::shared_ptr<RequestStorage> storage;
  std::vector<std::unique_ptr<ClientThread>> threads;

  int socketFd;

  // prevent copy
  ClientAgent(const ClientAgent&) = delete;
  ClientAgent& operator=(const ClientAgent&) = delete;

  static inline struct addrinfo getAddrInfoConfiguration() {
    struct addrinfo hi;
    memset(&hi, 0, sizeof(hi));
    hi.ai_family = AF_UNSPEC;
    hi.ai_socktype = SOCK_STREAM;
    hi.ai_flags = AI_PASSIVE;
    return hi;
  }

  inline struct addrinfo * getAddrInfo() const {
    struct addrinfo hi = getAddrInfoConfiguration();
    struct addrinfo *r;

    const char * port = configuration->getInPortString().c_str();
    if (0 != getaddrinfo(NULL, port, &hi, &r)) {
      HelperRoutines::error("ERROR getaddrinfo");
    }
    return r;
  }

  inline void listenSocket(const int socket) const {
    fprintf(stdout, "LISTEN\n");
    if (listen(socketFd, configuration->getInBacklog()) == -1) {
      HelperRoutines::error("listen ERROR");
    }
  }

  inline int bindSocket(struct addrinfo *r) const {
   int socket_fd;
   struct addrinfo *rorig;

    for (rorig = r; r != NULL; r = r->ai_next) {
      if (r->ai_family != AF_INET && r->ai_family != AF_INET6) continue;
      socket_fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
      if (-1 != socket_fd) {
        if (0 == bind(socket_fd, r->ai_addr, r->ai_addrlen)) {
          freeaddrinfo(rorig);
          return socket_fd;
        } else {
          close(socket_fd);
        }
      } else {
        HelperRoutines::warning("Opening socket failed");
      }
    }

    HelperRoutines::error("ERROR binding");
    freeaddrinfo(rorig);
    return -1;
  }

  inline void createPool() {
    for (int i = 0; i < configuration->getInPoolCount(); i++) {
      std::unique_ptr<ClientThread> p(new ClientThread(storage));
      threads.push_back(std::move(p));
    }
  }

  void doListen() {
    auto r = getAddrInfo();
    socketFd = bindSocket(r);
    listenSocket(socketFd);

    // deliver socket to threads
    for (auto it = threads.begin(); it != threads.end(); ++it) {
      (*it)->setSocket(socketFd);
    }
  }
};


#endif  // SRC_PROXY_CLIENTAGENT_H_
