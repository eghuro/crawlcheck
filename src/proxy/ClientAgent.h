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

class ClientThreadParameters {
 public:
  explicit ClientThreadParameters(std::shared_ptr<RequestStorage> stor) : sock(-1),
  storage(stor), work(true),
  connectionAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER),
  responseAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER),
  connectionMutex(PTHREAD_MUTEX_INITIALIZER) {
    std::cout << "New CTP" << std::endl;
  }

  virtual ~ClientThreadParameters() {
    std::cout << "Delete CTP" << std::endl;
  }

  void setConnection(int fd) {
    std::cout << "Set connection" << std::endl;
    std::cout << "Old socket:"<<sock<<" New socket:"<<fd << std::endl;
    sock = fd;
  }

  int getConnection() {
    return sock;
  }

  bool connectionAvailable() {}

  std::shared_ptr<RequestStorage> getStorage() {
    return storage;
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

  pthread_mutex_t * getConnectionMutex() {
    return &connectionMutex;
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
  int sock;
  bool work;
  pthread_mutex_t connectionAvailabilityMutex, responseAvailabilityMutex, workMutex, connectionMutex;
  pthread_cond_t connectionAvailabilityCondition, responseAvailabilityCondition;
  std::shared_ptr<RequestStorage> storage;

  ClientThreadParameters(const ClientThreadParameters&) = delete;
  ClientThreadParameters& operator=(const ClientThreadParameters&) = delete;
};

class ClientThread {
 public:
  explicit ClientThread(std::shared_ptr<RequestStorage> storage) {
    std::cout << "New CT" << std::endl;
    parameters = new ClientThreadParameters(storage);
    pthread_create(&thread, NULL, ClientThread::clientThreadRoutine, parameters);
  }

  virtual ~ClientThread() {
    std::cout << "Delete CT" << std::endl;
    pthread_join(thread, NULL);
    delete parameters;
  }

  void setSocket(int fd) {
    std::cout << "Set socket" << std::endl;
    std::cout << "Old: " << parameters->getConnection() << " New: " << fd << std::endl;

    pthread_mutex_t * cam = parameters->getConnectionAvailabilityMutex();
    pthread_mutex_t * cm = parameters->getConnectionMutex();

    pthread_mutex_lock(cam);
    pthread_mutex_lock(cm);
    parameters->setConnection(fd);
    pthread_mutex_unlock(cm);
    pthread_cond_broadcast(parameters->getConnectionAvailabilityCondition());
    pthread_mutex_unlock(cam);
    std::cout << "Done set socket" << std::endl;

  }
 private:
  pthread_t thread;
  static std::size_t buffer_size;

  ClientThread(const ClientThread&) = delete;
  ClientThread& operator=(const ClientThread&) = delete;

  ClientThreadParameters * parameters;
  static void * clientThreadRoutine(void * arg);
  static int establishConnection(ClientThreadParameters * parameters);
  static std::vector<std::size_t> request(const ClientThreadParameters *, int);
  static void response(const std::vector<std::size_t> &, const int, ClientThreadParameters *);
};

class ClientAgent{
public:

  ClientAgent(const std::shared_ptr<ProxyConfiguration> conf, std::shared_ptr<RequestStorage> store):
    threadCount(1), configuration(conf), storage(store) {
    threads = new ClientThread * [conf->getInPoolCount()];
  }

  virtual ~ClientAgent() {
    delete [] threads;
    close(socketFd);
  }

  void start() {
    for (int i = 0; i < threadCount; i++) {
      threads[i] = new ClientThread(storage);
    }

    auto r = getAddrInfo();
    socketFd = bindSocket(r);
    std::cout << socketFd << std::endl;

    fprintf(stdout, "LISTEN\n");
    if (listen(socketFd, configuration->getInBacklog()) == -1) {
      HelperRoutines::error("listen ERROR");
    }

    for (int i = 0; i < threadCount; i++) {
      threads[i]->setSocket(socketFd);
    }
  }

private:
  const int threadCount;
  int socketFd;
  ClientThread ** threads;
  const std::shared_ptr<ProxyConfiguration> configuration;
  const std::shared_ptr<RequestStorage> storage;

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

    std::string p(configuration->getInPortString());
    const char * port = p.c_str();
    if (0 != getaddrinfo(NULL, port, &hi, &r)) {
      freeaddrinfo(r);
      HelperRoutines::error("ERROR getaddrinfo");
    }
    return r;
  }

  inline int bindSocket(struct addrinfo *r) const {
    int socket_fd;
    struct addrinfo *rorig;

    std::cout << "BIND" << std::endl;

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
};



#endif  // SRC_PROXY_CLIENTAGENT_H_
