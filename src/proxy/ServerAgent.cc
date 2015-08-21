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
#include "ThreadedHelperRoutines.h"

std::size_t ServerThread::buffer_size = 1000;

void * ServerThread::serverThreadRoutine (void * arg) {
  HelperRoutines::info("Server thread routine");
  ServerWorkerParameters * parameters = reinterpret_cast<ServerWorkerParameters *>(arg);
  assert(parameters != nullptr);
  HelperRoutines::info("Trying to get storage");
  HelperRoutines::info("Get storage lock");
  pthread_mutex_t * storageLock = parameters->getStorageLock();
  assert (storageLock != nullptr);
  ThreadedHelperRoutines::lock(storageLock, "Storage lock");
  RequestStorage * storage = parameters->getStorage();
  ThreadedHelperRoutines::unlock(storageLock, "Storage lock");

  assert(storage != nullptr);
  HelperRoutines::info("Got storage");

  // pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS,NULL);
  while (parameters->doWork()) {
    //wait for request
    pthread_mutex_t * mutex = parameters->getRequestAvailabilityMutex();
    pthread_cond_t * condition = parameters->getRequestAvailabilityCondition();

    assert (storage != nullptr);
    assert (storage != NULL);

    ThreadedHelperRoutines::lock(storageLock, "Storage lock");
    storage->subscribeWait4Request(mutex, condition);
    ThreadedHelperRoutines::unlock(storageLock, "Storage lock");

    ThreadedHelperRoutines::lock(mutex, "Request availability mutex");

    HelperRoutines::info("Waiting for request");
    while(!storage->requestAvailable()) {
      pthread_cond_wait(condition, mutex);
    }
    HelperRoutines::info("Retrieving request");
    ThreadedHelperRoutines::lock(storageLock, "Storage lock");
    auto request = storage->retrieveRequest();
    ThreadedHelperRoutines::unlock(storageLock, "Storage lock");

    ThreadedHelperRoutines::unlock(mutex, "Request availability mutex");

    assert(std::get<0>(request).isRequest());
    std::string host = std::get<0>(request).getHost();
    int port = std::get<0>(request).getPort();

    //socket, connect
    int fd = ServerThread::connection(host, port);

    //write request
    ServerThread::writeRequest(request, fd, storage, storageLock);

    if (close(fd) != 0) HelperRoutines::warning("Close connection in server thread");
      else HelperRoutines::info(".. connection closed .. ");
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
        HelperRoutines::warning("READ response");
      } else {
        HttpParserResult result = parser.parse(std::string(buf, n));
        if (result.isResponse()) {
  // push DB
          ThreadedHelperRoutines::lock(storageLock, "Storage lock");
          (*storage).insertResponse(result, id);
          ThreadedHelperRoutines::unlock(storageLock, "Storage lock");
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
  if (0 != getaddrinfo(host.c_str(), HelperRoutines::to_string(port).c_str(), &hi, &r)) {
    freeaddrinfo(r);
    HelperRoutines::error("ERROR getaddrinfo");
  }
  int fd = -1;
  for (rorig = r; r != NULL; r=r->ai_next) {
    fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
    if (fd != -1) {
      if (connect(fd, (struct sockaddr *)r->ai_addr, r->ai_addrlen) == -1) {
        return fd;
      }
    } else {
      HelperRoutines::warning("Opening socket failed");
    }
  }
  freeaddrinfo(rorig);
  HelperRoutines::error("ERROR connecting");
  return -1;
}
