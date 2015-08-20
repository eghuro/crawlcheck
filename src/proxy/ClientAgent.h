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
    pthread_cond_init(&connectionAvailabilityCondition, NULL);
    pthread_cond_init(&responseAvailabilityCondition, NULL);
  }

  virtual ~ClientThreadParameters() {
    pthread_cond_destroy(&connectionAvailabilityCondition);
    pthread_cond_destroy(&responseAvailabilityCondition);
    std::cout << "Delete CTP" << std::endl;
  }

  void setConnection(int fd) {
    std::cout << "Set connection" << std::endl;
    sock = fd;
    std::cout << "Old socket:"<<sock<<" New socket:"<<fd << std::endl;
  }

  int getConnection() {
    return sock;
  }

  bool connectionAvailable() {
    return sock != -1;
  }

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
    int e = pthread_create(&thread, NULL, ClientThread::clientThreadRoutine, parameters);
    if (e != 0) {
      threadFailed = true;
      HelperRoutines::error(strerror(e));
    } else {
      threadFailed = false;
      std::cout << "new thread created" << std::endl;
    }
  }

  virtual ~ClientThread() {
    std::cout << "Delete CT" << std::endl;
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
  }

  void setSocket(int fd) {
    std::cout << "Set socket" << std::endl;
    std::cout << "Old: " << parameters->getConnection() << " New: " << fd << std::endl;

    pthread_mutex_t * cam = parameters->getConnectionAvailabilityMutex();
    pthread_mutex_t * cm = parameters->getConnectionMutex();

    int e;
    if ((e = pthread_mutex_lock(cam)) != 0) HelperRoutines::warning("Lock CAM", strerror(e));
    if ((e = pthread_mutex_lock(cm)) != 0) HelperRoutines::warning("Lock CM", strerror(e));
    parameters->setConnection(fd);
    if ((e = pthread_mutex_unlock(cm)) != 0) HelperRoutines::warning("Unlock CM", strerror(e));
    if ((e = pthread_cond_broadcast(parameters->getConnectionAvailabilityCondition())) != 0) HelperRoutines::warning("notify", strerror(e));
    if ((e = pthread_mutex_unlock(cam)) != 0) HelperRoutines::warning("Unlock CAM", strerror(e));
    std::cout << "Done set socket" << std::endl;

  }
 private:
  pthread_t thread;
  bool threadFailed;
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
    threadCount(conf->getInPoolCount()), configuration(conf), storage(store), socketFd(-1), threads(nullptr) {
    threads = new ClientThread * [conf->getInPoolCount()];
    for (int i = 0; i < conf->getInPoolCount(); i++) {
      threads[i] = nullptr;
    }
  }

  virtual ~ClientAgent() {
    std::cout << "CA dtor" << std::endl;
    if (threads != nullptr) {
      for (int i = 0; i < threadCount; i++) {
        if (threads[i] != nullptr) delete threads[i];
      }
    }
    //delete [] threads;
    if (socketFd>=0) close(socketFd);

  }

  void start() {
    for (int i = 0; i < threadCount; i++) {
      threads[i] = new ClientThread(storage);
    }

    auto r = getAddrInfo();
    socketFd = bindSocket(r);
    std::cout << socketFd << std::endl;

    for (int i = 0; i < threadCount; i++) {
      threads[i]->setSocket(socketFd);
    }

    fprintf(stdout, "LISTEN\n");
    if (listen(socketFd, configuration->getInBacklog()) == -1) {
      HelperRoutines::error("listen ERROR");
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
