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

class ProxyConfiguration {
 public:
  ProxyConfiguration():in_pool_count(0),  max_in(0), max_out(0),
    in_pool_port(-1), dbc_fd(-1), in_backlog(-1) {}

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

  void start() {
    struct addrinfo hi = getAddrInfo();
    struct addrinfo *r;

    const char * port = configuration.getInPortString().c_str();
    if (0 != getaddrinfo(NULL, port, &hi, &r)) {
      perror("ERROR getaddrinfo");
      exit(EXIT_FAILURE);
    }

    auto sockets = bindSockets(r);

    listenSockets(sockets);

    auto pollstr = sockets4poll(sockets);

    int timeout = -1;  // unlimited
    fprintf(stdout, "Polling ... %d\n",sockets.size());
    for(;;) {
      int poll_ret = poll(pollstr, sockets.size(), timeout);
      if (poll_ret > 0) {
        // success
        const std::size_t mask = POLLIN | POLLPRI;
        for (int i = 0; i < sockets.size(); i++) {
          if ( ((pollstr[i].revents & mask) == POLLIN) || ((pollstr[i].revents & mask) == POLLPRI) ) {
            handle(pollstr[i].fd);
          }
        }
      } else if (poll_ret == 0) {
    	// timeout
    	fprintf(stdout, "Connection timeout\n");
      } else {
    	perror("ERROR polling");
    	exit(EXIT_FAILURE);
      }
    }

    for(auto it = sockets.begin(); it!=sockets.end(); ++it) {
    	close(*it);
    }
  }

 private:
  const ProxyConfiguration & configuration;
  const Checker & checker;
  const Database & database;

  struct addrinfo getAddrInfo() {
    struct addrinfo hi;
    memset(&hi, 0, sizeof(hi));
    hi.ai_family = AF_UNSPEC;
    hi.ai_socktype = SOCK_STREAM;
    hi.ai_flags = AI_PASSIVE;
    return hi;
  }

  std::vector<int> bindSockets(struct addrinfo *r) {
	int socket_fd;
	std::vector<int> sockets;
	struct addrinfo *rorig;

	for (rorig = r; r != NULL; r = r->ai_next) {
	  if (r->ai_family != AF_INET && r->ai_family != AF_INET6) continue;
	  socket_fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
	  if (0 == bind(socket_fd, r->ai_addr, r->ai_addrlen)) {
	    sockets.push_back(socket_fd);
	  } else {
	    close(socket_fd);
	  }
	}
	if (sockets.size() == 0) {
	  perror("ERROR binding");
	  exit(EXIT_FAILURE);
	}
	freeaddrinfo(rorig);
	return sockets;
  }

  void listenSockets(const std::vector<int> & sockets) {
    for(auto it = sockets.begin(); it != sockets.end(); it++) {
	  fprintf(stdout, "LISTEN\n");
	  if (listen((*it), configuration.getInBacklog()) == -1) {
        perror("listen ERROR");
		exit(EXIT_FAILURE);
	  }
	}
  }

  struct pollfd * sockets4poll(const std::vector<int> & sockets) {
	  std::size_t size = sockets.size();
	  struct pollfd * array = new struct pollfd[size];

	  std::size_t index = 0;
	  for(auto it = sockets.begin(); it != sockets.end(); ++it, index++) {
		  array[index].fd = (*it);
		  array[index].events = POLLIN | POLLPRI;
		  fprintf(stdout, "%d\n", (*it));
	  }

	  return array;
  }

  void handle(int fd) {
    int new_fd = accept(fd, NULL, NULL);
    if (new_fd == -1) {
      perror("accept ERROR");
      exit(EXIT_FAILURE);
    }

    int buf_len = 1000;
    char buf[1000];
    fprintf(stderr, ".. connection accepted ..\n");
    int n;
    while ((n = read(new_fd, buf, buf_len)) != 0) {
      if (n == -1) {
    	perror("READ");
      } else {
        write(1, buf, n);
      }
    }
    close(new_fd);
    fprintf(stderr, ".. connection closed ..\n");
  }
};
#endif  // SRC_PROXY_PROXY_H_
