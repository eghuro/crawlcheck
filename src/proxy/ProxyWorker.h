// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_PROXYWORKER_H_
#define SRC_PROXY_PROXYWORKER_H_

#include <string.h>
#include <assert.h>
#include <pthread.h>
#include <err.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <memory>
#include <tuple>
#include <vector>
#include "./ProxyConfiguration.h"
#include "./HelperRoutines.h"
#include "./RequestStorage.h"
#include "../db/db.h"

/**
 * Connection identifiers are used to bond connections with client and server.
 * ConnectionIdentifierFactory generates a new such identifier.
 */
class ConnectionIdentifierFactory {
 public:
  typedef int identifier;

  /**
   * Get new identifier
   * @return new connection identifier
   */
  static identifier getId() {
    return next++;
  }
 private:
  static identifier next;
};

/**
 * ProxyWorker handles a single connection from client to a remote server
 */
class ProxyWorker {
 public:
  // TODO(alex): make singleton!
  explicit ProxyWorker(std::shared_ptr<ProxyConfiguration> config, std::shared_ptr<Database> db_ptr) :
    client_thread(0), server_thread(0), configuration(config),
    request_storage(std::make_shared<RequestStorage>(db_ptr)) {}
  virtual ~ProxyWorker();

  /**
   * Create a new pair of client & server threads to handle a single connection
   * @param fd a file descriptor of a socket to accept - connection with client
   */
  void startThread(int fd);

 private:
  typedef std::tuple<int, std::shared_ptr<RequestStorage>,
    std::shared_ptr<ProxyConfiguration>,
    ConnectionIdentifierFactory::identifier> parameter_type;

  pthread_t client_thread, server_thread;
  std::shared_ptr<RequestStorage> request_storage;
  std::shared_ptr<ProxyConfiguration> configuration;

  static const int buffer_size;

  static void* clientThreadRoutine(void * arg);
  static void* serverThreadRoutine(void * arg);
  static void handleClientRequest(int new_fd,
    std::shared_ptr<RequestStorage> storage,
    ConnectionIdentifierFactory::identifier id);
  static void handleClientResponse(int new_fd,
    std::shared_ptr<RequestStorage> storage,
    ConnectionIdentifierFactory::identifier id);

  void createThreads(void* parameter);

  static struct addrinfo getAddrInfoConfiguration() {
    struct addrinfo hi;
    memset(&hi, 0, sizeof(hi));
    hi.ai_family = AF_UNSPEC;
    hi.ai_socktype = SOCK_STREAM;
    hi.ai_flags = AI_PASSIVE;
    return hi;
  }

  static struct addrinfo * getAddrInfo(
    std::shared_ptr<ProxyConfiguration> conf) {

    struct addrinfo hi = getAddrInfoConfiguration();
    struct addrinfo *r;

    const char * port = conf->getInPortString().c_str();
    if (0 != getaddrinfo(NULL, port, &hi, &r)) {
      HelperRoutines::error("ERROR getaddrinfo");
    }
    return r;
  }

  static std::vector<int> getSockets(struct addrinfo * r) {
    int socket_fd;
    std::vector<int> sockets;
    struct addrinfo *rorig;

    for (rorig = r; r != NULL; r = r->ai_next) {
      if (r->ai_family != AF_INET && r->ai_family != AF_INET6) continue;
      socket_fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
      if (socket_fd != -1) {
        sockets.push_back(socket_fd);
      } else {
        HelperRoutines::warning("Opening socket failed");
      }
    }

    freeaddrinfo(rorig);
    return sockets;
  }
};
#endif  // SRC_PROXY_PROXYWORKER_H_
