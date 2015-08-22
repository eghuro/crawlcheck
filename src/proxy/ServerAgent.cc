// Copyright 2015 Alexandr Mansurov
#include "ServerAgent.h"
#include <unistd.h>
#include <pthread.h>
#include <poll.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <memory>
#include <cassert>
#include "./RequestStorage.h"
#include "ThreadedHelperRoutines.h"

const std::size_t ServerThread::in_buffer_size = 1000;
const std::size_t ServerThread::out_buffer_size = 100;

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

  //wait for request
  //pthread_mutex_t * mutex = parameters->getRequestAvailabilityMutex();
  //pthread_cond_t * condition = parameters->getRequestAvailabilityCondition();
  //ThreadedHelperRoutines::lock(storageLock, "Storage lock");
  //storage->subscribeWait4Request(mutex, condition);
  //ThreadedHelperRoutines::unlock(storageLock, "Storage lock");

  while (true){//parameters->doWork()) {
    // wait for request
    //ThreadedHelperRoutines::lock(mutex, "Request availability mutex");
    HelperRoutines::info("Waiting for request");
    wait4request(storage); //nezamcena storage
    HelperRoutines::info("Retrieving request");
    ThreadedHelperRoutines::lock(storageLock, "Storage lock");
    auto request = storage->retrieveRequest();
    ThreadedHelperRoutines::unlock(storageLock, "Storage lock");

    //ThreadedHelperRoutines::unlock(mutex, "Request availability mutex");

    //assert(std::get<0>(request).isRequest());
    std::string host = std::get<0>(request).getHost();
    int port = std::get<0>(request).getPort();

    HelperRoutines::info(host);
    HelperRoutines::info(HelperRoutines::to_string(port));

    //socket, connect
    int fd = ServerThread::connection(host, port);

    HelperRoutines::info(HelperRoutines::to_string(fd));

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
  const char * data = raw_request.c_str();
  const std::size_t size = strlen(data);
  const char * buf_ptr = data;
  int n, sum = 0;
  bool writeFailed = false;

  // write request
  while ((sum < size) && !writeFailed) {
    n = write(fd, buf_ptr+sum, ServerThread::out_buffer_size);
    if (n == -1) { HelperRoutines::warning("Write request"); writeFailed = true; }
    else if (n > 0) {
      sum += n;
    }
  }

  // read response
  if (!writeFailed) {
  // read response
    HttpParser parser;
    std::stringstream oss;
    char buf[ServerThread::in_buffer_size];
    bool readFailed = false;
    int n;
    while ((n = read(fd, buf, ServerThread::in_buffer_size)) != 0) {
      if (n == -1) {
        readFailed = true;
        HelperRoutines::warning("READ response");
      } else {
        oss<<buf;
      }
    }

    if (!readFailed) {
      std::cout << oss.str();
      HttpParserResult result = parser.parse(oss.str());
      if (result.isResponse()) {
// push DB
        ThreadedHelperRoutines::lock(storageLock, "Storage lock");
        (*storage).insertResponse(result, id);
        ThreadedHelperRoutines::unlock(storageLock, "Storage lock");
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
    //freeaddrinfo(r);
    HelperRoutines::error("ERROR getaddrinfo");
  }
  int fd = -1;
  for (rorig = r; r != NULL; r=r->ai_next) {
    if (r->ai_family != AF_INET && r->ai_family != AF_INET6)
          continue;
    fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
    if (fd != -1) {
      if (connect(fd, (struct sockaddr *)r->ai_addr, r->ai_addrlen) == 0) {
        return fd;
      }
    } else {
      HelperRoutines::warning("Opening socket failed");
    }
  }
  //freeaddrinfo(rorig);
  HelperRoutines::error("ERROR connecting");
  return -1;
}
