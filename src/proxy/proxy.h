// Copyright 2015 Alexandr Mansurov
#ifndef SRC_PROXY_PROXY_H_
#define SRC_PROXY_PROXY_H_

#include <sys/types.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <netdb.h>
#include <unistd.h>
#include <assert.h>
#include <poll.h>
#include <string>
#include <vector>
#include <memory>
#include "../checker/checker.h"
#include "../db/db.h"
#include "./ProxyWorker.h"
#include "./HelperRoutines.h"
#include "./ProxyConfiguration.h"

/**
 * Proxy server.
 * Crawlcheck's user interface is a transparent HTTP proxy. A tester can do
 * manual verifications of content while automated software verification is
 * ongoing in background.
 *
 * The proxy server is implemented in Proxy class. This class handles network
 * communication with client (tester) and server (the website under test) and
 * among others passes the data in transit for further inspection to other
 * related modules.
 *
 * For creating a Proxy you need a ProxyConfiguration instance, a Checker and a
 * Database. Proxy is then started invoking start() method. Listening socket
 * will be created and on incoming connections a separate thread is started.
 * Connections to the web server for passing requests are initiated in the
 * connection threads.
 */
class Proxy {
 public:
  /**
   * Create a Proxy.
   * No special preconditions on provided pointers and references.
   *
   * @param conf a pointer to ProxyConfiguration object containing the config
   * @param check a reference to Checker that is not in use at the moment
   * @param db a reference to Database that is not in use at the moment
   */
  // TODO(alex): update docs when checker and db are in use
  Proxy(std::shared_ptr<ProxyConfiguration> conf, const Checker & check,
    const Database & db): configuration(conf), checker(check), database(db) {}

  /**
   * Entry point for proxy.
   * Creates sockets, listens and eventually accepts an incoming connection.
   * The connection is then handled with a ProxyWorker
   */
  void start();

 private:
  const std::shared_ptr<ProxyConfiguration> configuration;
  const Checker & checker;
  const Database & database;

  /**
   * Create listening sockets on all interfaces and bind them.
   * @param r addrinfo
   * @return list of file descriptors with binded sockets
   */
  static std::vector<int> bindSockets(struct addrinfo *r);

  /**
   * Transform vector of file descriptors to a data structure needed in
   * poll function.
   * @param sockets file descriptors in a vector
   * @return file descriptors as needed in poll
   */
  static struct pollfd * sockets4poll(const std::vector<int> & sockets);

  /**
   * set up initial addrinfo for getaddrinfo
   * @return settings: family independent, TCP, passive
   */
  static inline struct addrinfo getAddrInfoConfiguration() {
    struct addrinfo hi;
    memset(&hi, 0, sizeof(hi));
    hi.ai_family = AF_UNSPEC;
    hi.ai_socktype = SOCK_STREAM;
    hi.ai_flags = AI_PASSIVE;
    return hi;
  }

  /**
   * set up addrinfo for socket
   * @return addrinfo on the port specified in configuration
   * on failure announce error via HelperRoutines
   */
  inline struct addrinfo * getAddrInfo() {
    struct addrinfo hi = getAddrInfoConfiguration();
    struct addrinfo *r;

    const char * port = configuration->getInPortString().c_str();
    if (0 != getaddrinfo(NULL, port, &hi, &r)) {
      HelperRoutines::error("ERROR getaddrinfo");
    }
    return r;
  }

  /**
   * listens on the provided file descriptors with backlog specified in config
   * @param sockets file descriptors to listen at
   * on failure announce error via HelperRoutines
   */
  inline void listenSockets(const std::vector<int> & sockets) {
    for (auto it = sockets.begin(); it != sockets.end(); it++) {
      fprintf(stdout, "LISTEN\n");
      if (listen((*it), configuration->getInBacklog()) == -1) {
        HelperRoutines::error("listen ERROR");
      }
    }
  }

  /**
   * Handle a new connection.
   * fire up a ProxyWorker and start a new thread to handle an incoming
   * connection.
   * @param fd file descriptor of the server socket
   * @param config_ptr proxy configuration
   */
  static void handle(int fd, std::shared_ptr<ProxyConfiguration> config_ptr) {
    ProxyWorker pw(config_ptr);
    pw.startThread(fd);
  }
};
#endif  // SRC_PROXY_PROXY_H_
