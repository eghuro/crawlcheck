// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_PROXYCONFIGURATION_H_
#define SRC_PROXY_PROXYCONFIGURATION_H_

#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include "./HelperRoutines.h"

class ProxyConfiguration {
 public:
  ProxyConfiguration():in_pool_count(0),  max_in(0), max_out(0),
    in_pool_port(-1), dbc_fd(-1), in_backlog(-1) {}
  virtual ~ProxyConfiguration() {}

  inline bool setPoolCount(int count) {
    if (count >= 0) {
      in_pool_count = count;
      return true;
    }
    return false;
  }

  inline bool setMaxIn(int max) {
    if (max >= 0) {
      max_in = max;
      return true;
    }
    return false;
  }

  inline bool setMaxOut(int max) {
    if (max >= 0) {
      max_out = max;
      return true;
    }
    return false;
  }

  inline bool setInPoolPort(int port) {
    if (acceptablePort(port)) {
      in_pool_port = port;
      return true;
    }
    return false;
  }

  inline bool setDbcFd(int fd) {
    if (fd >= 0) {
      dbc_fd = fd;
      return true;
    } else {
      return false;
    }
  }

  inline bool setInBacklog(int count) {
    if (count > SOMAXCONN) {
      count = SOMAXCONN;
      // TODO(alex): ohlasit?
    }
    if (count >= 0) {
      in_backlog = count;
      return true;
    }
    return false;
  }

  inline int getPoolCount() const {
    return in_pool_count;
  }

  inline int getMaxIn() const {
    return max_in;
  }

  inline int getMaxOut() const {
    return max_out;
  }

  inline int getInPoolPort() const {
    return in_pool_port;
  }

  inline int getDbcFd() const {
    return dbc_fd;
  }

  inline int getInBacklog() const {
    return in_backlog;
  }

  inline std::string getInPortString() const {
    return HelperRoutines::to_string(in_pool_port);
  }

 private:
  int in_pool_count;
  int max_in, max_out;
  int in_pool_port;
  int dbc_fd;
  int in_backlog;

  inline bool acceptablePort(int port) {
    return (port > 0) && (port <= 65535);
  }
};

#endif  // SRC_PROXY_PROXYCONFIGURATION_H_
