// Copyright 2015 Alexandr Mansurov
#include "ServerAgent.h"
#include <unistd.h>
#include <pthread.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <memory>
#include <cassert>
#include "./RequestStorage.h"

std::size_t ServerThread::buffer_size = 1000;

void * ServerThread::serverThreadRoutine (void * arg) {
  std::cout << "Server thread routine" << std::endl;
  ServerWorkerParameters * parameters = reinterpret_cast<ServerWorkerParameters *>(arg);
  assert(parameters != nullptr);

  std::cout << "Get storage lock" << std::endl;
  pthread_mutex_t * storageLock = parameters->getStorageLock();
  assert (storageLock != nullptr);

  std::cout << "Trying to get storage" << std::endl;
  int e = pthread_mutex_lock(storageLock);
  if (e != 0) {
    std::cout << strerror(e)  <<std::endl;
  }
  RequestStorage * storage = parameters->getStorage();
  pthread_mutex_unlock(storageLock);

  assert(storage != nullptr);
  std::cout << "Got storage" << std::endl;

  pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS,NULL);
  while (parameters->doWork()) {
    //wait for request
    pthread_mutex_t * mutex = parameters->getRequestAvailabilityMutex();
    pthread_cond_t * condition = parameters->getRequestAvailabilityCondition();

    assert (storage != nullptr);
    assert (storage != NULL);

    pthread_mutex_lock(storageLock);
    storage->subscribeWait4Request(mutex, condition);
    pthread_mutex_unlock(storageLock);
    pthread_mutex_lock(mutex);
    std::cout << "Waiting for request" <<std::endl;
    while(!storage->requestAvailable()) {
      pthread_cond_wait(condition, mutex);
    }
    std::cout << "Retrieving request" <<std::endl;
    pthread_mutex_lock(storageLock);
    auto request = storage->retrieveRequest();
    pthread_mutex_unlock(storageLock);
    pthread_mutex_unlock(mutex);

    assert(std::get<0>(request).isRequest());
    std::string host = std::get<0>(request).getHost();
    int port = std::get<0>(request).getPort();

    //socket, connect
    int fd = ServerThread::connection(host, port);

    //write request
    ServerThread::writeRequest(request, fd, storage, storageLock);

    close(fd);
  }
  delete parameters;
}

void ServerThread::writeRequest(const RequestStorage::queue_type & request, const int fd,
    RequestStorage* storage, pthread_mutex_t * storageLock) {
  std::string raw_request = std::get<0>(request).getRaw();
  auto id = std::get<1>(request);
  if (write(fd, raw_request.c_str(), raw_request.size()) != -1) {
  // read response
    HttpParser parser;
    char buf[ServerThread::buffer_size];
    int n;
    while ((n = read(fd, buf, ServerThread::buffer_size)) != 0) {
      if (n == -1) {
        perror("READ response");
      } else {
        HttpParserResult result = parser.parse(std::string(buf, n));
        if (result.isResponse()) {
  // push DB
          pthread_mutex_lock(storageLock);
          (*storage).insertResponse(result, id);
          pthread_mutex_unlock(storageLock);
        }
      }
    }
  }
}

int ServerThread::connection (const std::string & host, const int port) {
  struct addrinfo *r, *rorig, hi;
  memset(&hi, 0, sizeof (hi));
  hi.ai_family = AF_UNSPEC;
  hi.ai_socktype = SOCK_STREAM;
  getaddrinfo(host.c_str(), HelperRoutines::to_string(port).c_str(), &hi, &r);
  int fd = -1;
  for (rorig = r; r != NULL; r=r->ai_next) {
    fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
    if (connect(fd, (struct sockaddr *)r->ai_addr, r->ai_addrlen) == -1) {
      return fd;
    }
  }
  freeaddrinfo(rorig);
}
