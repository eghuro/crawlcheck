#ifndef CRAWLCHECK_PROXY_PROXY_H
#define CRAWLCHECK_PROXY_PROXY_H

#include "checker/checker.h"
#include "db/db.h"
#include <sys/types.h>
#include <sys/socket.h>
#include <stdlib.h>

class ProxyConfiguration {
 public:
  ProxyConfiguration():in_pool_count(0),  max_in(0), max_out(0), 
    in_pool_port(-1), dbc_fd(-1){};

  void setPoolCount(int count) {
    if (count >= 0) {
      in_pool_count = count;
    }
    //TODO(alex): co, kdyz ne?
  }

  void setMaxIn(int max) {
    if (max >= 0) {
      max_in = max;
    }
    //TODO(alex): co, kdyz ne?
  }

  void setMaxOut(int out) {
    if (out >= 0) {
      max_out = out;
    }
    //TODO(alex): co, kdyz ne?
  }

  void setInPoolPort(int port) {
    if (acceptablePort(port)) {
      in_pool_port = port;
    }
    //TODO(alex): co, kdyz ne?
  }

  void setDbcFd(int fd) {
    //TODO(alex): kontroly?
    dbc_fd = fd;
  }

  void setInBacklog(int count) {
    if (count > SOMAXCONN) {
      count = SOMAXCONN;
    }
    if (count >= 0) {
      in_backlog = count;
    }
    //TODO(alex): co, kdyz ne?
  }

  int getPoolCount() {
    return in_pool_count;
  }

  int getMaxIn() {
    return max_in;
  }

  int getMaxOut() {
    return max_out;
  }

  int getInPoolPort() {
    return in_pool_port;
  }

  int getDbcFd() {
    return dbc_fd;
  }

  int getInbacklog() {
    return in_backlog;
  }
 private:
  int in_pool_count;
  int max_in, max_out;
  int in_pool_port;
  int dbc_fd;
  int in_backlog;

  bool acceptablePort(int port) {
    return port > 0;  //TODO(alex): detailnejsi kontrola?
  }
};

class Proxy {
 public:
  Proxy(const ProxyConfiguration & conf, const Checker & check, 
   const Database & db): configuration(conf), checker(check), database(db){};
  
  void start() {
    // socket
    int socket_fd = socket(AF_INET6, SOCK_STREAM | SOCK_NONBLOCK, 0);
    if (socket_fd == -1) {
      perror("ERROR opening socket");
      exit(EXIT_FAILURE);
    }
    
    // bind
    struct sockaddr in_addr;
    bzero((char *) &in_addr), sizeof(in_addr));
    in_addr.sin_faminly = AF_INET6;
    in_addr.sin_addr.s_addr = in6addr_any;
    in_addr.sin_port = htons(conf.getInPoolPort());

    if (bind(socket_fd, (struct sockaddr *) &in_addr, sizeof(inaddr)) != 0) {
      perror("ERROR on binding");
      exit(EXIT_FAILURE);
    }

    // listen
   if (listen(socket_fd, conf.getInBacklog()) != 0) {
     perror("ERROR on listen");
     exit(EXIT_FAILURE);
   }

    // nekolik vlaken/procesu delaji accept
  }
 private:
  const ProxyConfiguration & configuration;
  const Checker & checker;
  const Database & database;
};
#endif //CRAWLCHECK_PROXY_PROXY_H
