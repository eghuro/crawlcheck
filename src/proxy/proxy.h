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
#include "../checker/checker.h"
#include "../db/db.h"
#include "./ProxyWorker.h"
#include "./HelperRoutines.h"

class ProxyConfiguration {
 public:
  ProxyConfiguration():in_pool_count(0),  max_in(0), max_out(0),
    in_pool_port(-1), dbc_fd(-1), in_backlog(-1) {}
  virtual ~ProxyConfiguration() {}

  void setPoolCount(int count) {
    if (count >= 0) {
      in_pool_count = count;
    }
    // TODO(alex): co, kdyz ne?
  }

  void setMaxIn(int max) {
    if (max >= 0) {
      max_in = max;
    }
    // TODO(alex): co, kdyz ne?
  }

  void setMaxOut(int out) {
    if (out >= 0) {
      max_out = out;
    }
    // TODO(alex): co, kdyz ne?
  }

  void setInPoolPort(int port) {
    if (acceptablePort(port)) {
      in_pool_port = port;
    }
    // TODO(alex): co, kdyz ne?
  }

  void setDbcFd(int fd) {
    // TODO(alex): kontroly?
    dbc_fd = fd;
  }

  void setInBacklog(int count) {
    if (count > SOMAXCONN) {
      count = SOMAXCONN;
    }
    if (count >= 0) {
      in_backlog = count;
    }
    // TODO(alex): co, kdyz ne?
  }

  int getPoolCount() const {
    return in_pool_count;
  }

  int getMaxIn() const {
    return max_in;
  }

  int getMaxOut() const {
    return max_out;
  }

  int getInPoolPort() const {
    return in_pool_port;
  }

  int getDbcFd() const {
    return dbc_fd;
  }

  int getInBacklog() const {
    return in_backlog;
  }

  std::string getInPortString() const {
    return std::to_string(in_pool_port);
  }

 private:
  int in_pool_count;
  int max_in, max_out;
  int in_pool_port;
  int dbc_fd;
  int in_backlog;

  bool acceptablePort(int port) {
    return port > 0;  // TODO(alex): detailnejsi kontrola?
  }
};

class Proxy {
 public:
  Proxy(const ProxyConfiguration & conf, const Checker & check,
    const Database & db): configuration(conf), checker(check), database(db) {}

  void start();

 private:
  const ProxyConfiguration & configuration;
  const Checker & checker;
  const Database & database;

  static std::vector<int> bindSockets(struct addrinfo *r);
  static struct pollfd * sockets4poll(const std::vector<int> & sockets);

  static struct addrinfo getAddrInfo() {
    struct addrinfo hi;
    memset(&hi, 0, sizeof(hi));
    hi.ai_family = AF_UNSPEC;
    hi.ai_socktype = SOCK_STREAM;
    hi.ai_flags = AI_PASSIVE;
    return hi;
  }

  void listenSockets(const std::vector<int> & sockets) {
    for (auto it = sockets.begin(); it != sockets.end(); it++) {
      fprintf(stdout, "LISTEN\n");
      if (listen((*it), configuration.getInBacklog()) == -1) {
        HelperRoutines::error("listen ERROR");
      }
    }
  }

  static void handle(int fd) {
    ProxyWorker pw;
    pw.startThread(fd);
  }
};
#endif  // SRC_PROXY_PROXY_H_
