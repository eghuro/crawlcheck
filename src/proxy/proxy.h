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

class Proxy {
 public:
  Proxy(std::shared_ptr<ProxyConfiguration> conf, const Checker & check,
    const Database & db): configuration(conf), checker(check), database(db) {
  }

  void start();

 private:
  const std::shared_ptr<ProxyConfiguration> configuration;
  const Checker & checker;
  const Database & database;

  static std::vector<int> bindSockets(struct addrinfo *r);
  static struct pollfd * sockets4poll(const std::vector<int> & sockets);

  static struct addrinfo getAddrInfoConfiguration() {
	struct addrinfo hi;
	memset(&hi, 0, sizeof(hi));
	hi.ai_family = AF_UNSPEC;
	hi.ai_socktype = SOCK_STREAM;
	hi.ai_flags = AI_PASSIVE;
	return hi;
  }

  struct addrinfo * getAddrInfo() {
    struct addrinfo hi = getAddrInfoConfiguration();
    struct addrinfo *r;

    const char * port = configuration->getInPortString().c_str();
    if (0 != getaddrinfo(NULL, port, &hi, &r)) {
      HelperRoutines::error("ERROR getaddrinfo");
    }
    return r;
  }

  void listenSockets(const std::vector<int> & sockets) {
    for (auto it = sockets.begin(); it != sockets.end(); it++) {
      fprintf(stdout, "LISTEN\n");
      if (listen((*it), configuration->getInBacklog()) == -1) {
        HelperRoutines::error("listen ERROR");
      }
    }
  }

  static void handle(int fd, std::shared_ptr<ProxyConfiguration> config_ptr) {
    ProxyWorker pw(config_ptr);
    pw.startThread(fd);
  }
};
#endif  // SRC_PROXY_PROXY_H_
