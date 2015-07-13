#ifndef CRAWLCHECK_PROXY_PROXY_H
#define CRAWLCHECK_PROXY_PROXY_H

#include "../checker//checker.h"
#include "../db/db.h"
#include <string>
#include <sys/types.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <netdb.h>
#include <unistd.h>
#include <assert.h>

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
    return port > 0;  //TODO(alex): detailnejsi kontrola?
  }
};

class Proxy {
 public:
  Proxy(const ProxyConfiguration & conf, const Checker & check, 
   const Database & db): configuration(conf), checker(check), database(db){};
  
  void start() {
    struct addrinfo hi;
    memset(&hi, 0, sizeof(hi));
    hi.ai_family = AF_UNSPEC;
    hi.ai_socktype = SOCK_STREAM;
    hi.ai_flags = AI_PASSIVE;

    struct addrinfo *r, *rorig;

    fprintf(stdout, "GETADDRINFO\n");
    if (0 != getaddrinfo(NULL, configuration.getInPortString().c_str(), &hi, &r)) {
      perror("ERROR getaddrinfo");
      exit(EXIT_FAILURE);
    }

    fprintf(stdout,"SOCKET\n");
    int socket_fd;
    for (rorig = r; r != NULL; r = r->ai_next) {
      socket_fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
      if (0 != bind(socket_fd, r->ai_addr, r->ai_addrlen)) break;
    }
    freeaddrinfo(rorig);
    if (r == nullptr) {
      perror("ERROR binding");
      exit(EXIT_FAILURE);
    }
    
    fprintf(stdout, "LISTEN\n");
    if (listen(socket_fd, configuration.getInBacklog()) == -1) {
      perror("listen ERROR");
      exit(EXIT_FAILURE);
    }
    struct sockaddr_storage ca;
    for (;;) {
      fprintf(stdout, "ACCEPT\n");
      auto sz = sizeof(ca);
      int new_fd = accept(socket_fd, (struct sockaddr *)&ca, &sz);
      if (new_fd == -1) {
        perror("accept ERROR");
        exit(EXIT_FAILURE);
      }
      /* komunikace s klientem */
      int buf_len = 1000;
      char buf[1000];
      fprintf(stderr, ".. connection accepted ..\n");
      int n;
      while ((n = read(new_fd, buf, buf_len)) != 0) {
        write(1, buf, n);
      }

      close(new_fd);
      fprintf(stderr, ".. connection closed ..\n");
    }
  }
 private:
  const ProxyConfiguration & configuration;
  const Checker & checker;
  const Database & database;
};
#endif //CRAWLCHECK_PROXY_PROXY_H
