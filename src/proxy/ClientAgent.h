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
#include "ThreadedHelperRoutines.h"
#include "ProxyConfiguration.h"

class Bundle {
 public:
  static pthread_mutex_t stop_lock;
  static bool stop;
  static pthread_cond_t * stop_cond;
  static pthread_t * stop_thread;

  static void* stopThreadRoutine(void *) {
    HelperRoutines::info("Client process caught a signal and started a stop thread");
    ThreadedHelperRoutines::lock(&Bundle::stop_lock, "Lock stop");
    Bundle::stop = true;
    pthread_cond_broadcast(Bundle::stop_cond);
    ThreadedHelperRoutines::unlock(&Bundle::stop_lock, "Unlock stop");
    HelperRoutines::info("Leaving stop thread");
  }
};

class ClientThreadParameters {
 public:
  ClientThreadParameters(RequestStorage * stor, pthread_mutex_t * storeLock) : sock(-1),
  storage(stor), storageMutex(storeLock), connectionAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER),
  responseAvailabilityMutex(PTHREAD_MUTEX_INITIALIZER), connectionMutex(PTHREAD_MUTEX_INITIALIZER) {
    HelperRoutines::info("New ClientThreadParameters");
    int e = pthread_cond_init(&connectionAvailabilityCondition, NULL);
    if (e != 0) HelperRoutines::warning("Initialize condition variable (connection availability)", strerror(e));
    e = pthread_cond_init(&responseAvailabilityCondition, NULL);
    if (e != 0) HelperRoutines::warning("Initialize condition variable (response availability)", strerror(e));
  }

  virtual ~ClientThreadParameters() {
    int e = pthread_cond_destroy(&connectionAvailabilityCondition);
    if (e != 0) HelperRoutines::warning("Destroy condition variable (connection availability)", strerror(e));
    e = pthread_cond_destroy(&responseAvailabilityCondition);
    if (e != 0) HelperRoutines::warning("Destroy condition variable (response availability)", strerror(e));
    HelperRoutines::info("Delete ClientThreadParameters");
  }

  void setConnection(int fd) {
    HelperRoutines::info("Set connection");
    sock = fd;
    std::ostringstream oss;
    oss << "New socket:"<<fd;
    HelperRoutines::info(oss.str());
  }

  int getConnection() {
    return sock;
  }

  bool connectionAvailable() {
    return sock != -1;
  }

  pthread_mutex_t * getConnectionAvailabilityMutex() {
    return &connectionAvailabilityMutex;
  }

  bool connectionAvailable() const {
    return sock >= 0;
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

  RequestStorage* getStorage() const {
    return storage;
  }

  pthread_mutex_t * getStorageLock() {
    return storageMutex;
  }

 private:
  int sock;
  pthread_mutex_t connectionAvailabilityMutex, responseAvailabilityMutex, connectionMutex;
  pthread_cond_t connectionAvailabilityCondition, responseAvailabilityCondition;
  RequestStorage * storage;
  pthread_mutex_t * storageMutex;

  ClientThreadParameters(const ClientThreadParameters&) = delete;
  ClientThreadParameters& operator=(const ClientThreadParameters&) = delete;
};

class ClientThread {
 public:
  ClientThread(RequestStorage* storage, pthread_mutex_t * storageLock) :
    parameters(nullptr), stopped(false) {
    HelperRoutines::info("New CT");
    parameters = new ClientThreadParameters(storage, storageLock);
    assert(parameters != nullptr);
    start();
  }

  virtual ~ClientThread() {
    HelperRoutines::info("Delete CT");
    if (!stopped) {
      stop();
    }
    delete parameters;
  }

  void start() {
    int e = pthread_create(&thread, NULL, ClientThread::clientThreadRoutine, parameters);
    if (e != 0) {
      HelperRoutines::error(strerror(e));
    } else {
      HelperRoutines::info("new client thread created");
    }
  }

  void stop() {
    HelperRoutines::info("CT stop");

    // this should be shared
    bool stop = false;
    pthread_mutex_t stop_lock(PTHREAD_MUTEX_INITIALIZER);
    pthread_cond_t stop_cond(PTHREAD_COND_INITIALIZER);
    //int er = pthread_cond_init(stop_cond, NULL);
    //if (er != 0) HelperRoutines::warning("Initialize condition variable (stop condition)", strerror(er));

    ThreadedHelperRoutines::lock(&stop_lock, "Lock stop lock");
    while(!stop) {
      pthread_cond_wait(&stop_cond, &stop_lock);
    }
    HelperRoutines::info("Join");
    int e = pthread_join(thread, NULL);
    if (e != 0) {
      HelperRoutines::warning("Pthread_join", strerror(e));
    } else {
      HelperRoutines::info("Join successful");
      stopped = true;
    }
    ThreadedHelperRoutines::unlock(&stop_lock, "Unlock stop lock");
  }

  void setSocket(int fd) {
    HelperRoutines::info("Set socket");
    HelperRoutines::info(HelperRoutines::to_string(fd));

    HelperRoutines::info(HelperRoutines::to_string(parameters->getConnection()));

    pthread_mutex_t * cam = parameters->getConnectionAvailabilityMutex();
    pthread_mutex_t * cm = parameters->getConnectionMutex();

    assert(cam != nullptr);
    assert(cm != nullptr);

    ThreadedHelperRoutines::lock(cam, "CAM");
    ThreadedHelperRoutines::lock(cm, "CM");
    parameters->setConnection(fd);
    ThreadedHelperRoutines::unlock(cm, "CM");
    ThreadedHelperRoutines::broadcast(parameters->getConnectionAvailabilityCondition(), "Notify");
    ThreadedHelperRoutines::unlock(cam, "CAM");
    HelperRoutines::info("Done set socket");

  }

 private:
  pthread_t thread;
  bool stopped;
  ClientThreadParameters * parameters;

  ClientThread(const ClientThread&) = delete;
  ClientThread& operator=(const ClientThread&) = delete;

  static std::size_t in_buffer_size;
  static std::size_t out_buffer_size;
  static void * clientThreadRoutine(void * arg);
  static int establishConnection(ClientThreadParameters * parameters);
  static std::vector<std::size_t> request(ClientThreadParameters *, int);
  static void response(const std::vector<std::size_t> &, const int, ClientThreadParameters *);
};

class ClientAgent{
public:
  ClientAgent(const std::shared_ptr<ProxyConfiguration> conf, RequestStorage* store, pthread_mutex_t * storeLock):
    threadCount(conf->getInPoolCount()), configuration(conf), storage(store),storageLock(storeLock), socketFd(-1) {
    HelperRoutines::info("Creating ClientAgent");
    std::ostringstream oss;
    oss << "Threads: "<<conf->getInPoolCount();
    HelperRoutines::info(oss.str());

    threads = new ClientThread * [threadCount];
    for (int i = 0; i < threadCount; i++) {
      threads[i] = nullptr;
    }
  }

  virtual ~ClientAgent() {
    HelperRoutines::info("CA dtor");
    delete [] threads;
  }

  void start() {
    for (int i = 0; i < threadCount; i++) {
      threads[i] = new ClientThread(storage, storageLock);
       HelperRoutines::info("Created a thread");
     }

    auto r = getAddrInfo();
    socketFd = bindSocket(r);
    HelperRoutines::info(HelperRoutines::to_string(socketFd));

    std::ostringstream oss;
    for (int i = 0; i < threadCount; i++) {
      oss << "Set socket for thread "<< i;
      HelperRoutines::info(oss.str());
      threads[i]->setSocket(socketFd);
    }

    HelperRoutines::info("LISTEN");
    if (listen(socketFd, configuration->getInBacklog()) == -1) {
      HelperRoutines::error("listen ERROR");
    }
  }

  void stop() {
    for (int i = 0; i < threadCount; i++) {
      threads[i]->stop();
    }

    if (socketFd>=0) close(socketFd);
  }

private:
  const int threadCount;
  int socketFd;
  ClientThread ** threads;
  pthread_mutex_t * storageLock;
  const std::shared_ptr<ProxyConfiguration> configuration;
  RequestStorage * storage;

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
      HelperRoutines::error("ERROR getaddrinfo");
    }
    return r;
  }

  inline int bindSocket(struct addrinfo *r) const {
    int socket_fd;
    struct addrinfo *rorig;

    HelperRoutines::info("BIND");

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

    freeaddrinfo(rorig);
    HelperRoutines::error("ERROR binding");
    return -1;
  }
};
#endif  // SRC_PROXY_CLIENTAGENT_H_
