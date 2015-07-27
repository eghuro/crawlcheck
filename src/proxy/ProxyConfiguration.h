// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_PROXYCONFIGURATION_H_
#define SRC_PROXY_PROXYCONFIGURATION_H_

#include <sys/socket.h>
#include <string>
#include "./HelperRoutines.h"

class ProxyConfiguration {
 public:
  ProxyConfiguration():in_pool_count(0),  max_in(0), max_out(0),
    in_pool_port(-1), dbc_fd(-1), in_backlog(-1) {}
  virtual ~ProxyConfiguration() {}

  inline void setPoolCount(int count) {
    if (count >= 0) {
      in_pool_count = count;
    }
    // TODO(alex): co, kdyz ne?
  }

  inline void setMaxIn(int max) {
    if (max >= 0) {
      max_in = max;
    }
    // TODO(alex): co, kdyz ne?
  }

  inline void setMaxOut(int out) {
    if (out >= 0) {
      max_out = out;
    }
    // TODO(alex): co, kdyz ne?
  }

  inline void setInPoolPort(int port) {
    if (acceptablePort(port)) {
      in_pool_port = port;
    }
    // TODO(alex): co, kdyz ne?
  }

  inline void setDbcFd(int fd) {
    // TODO(alex): kontroly?
    dbc_fd = fd;
  }

  inline void setInBacklog(int count) {
    if (count > SOMAXCONN) {
      count = SOMAXCONN;
    }
    if (count >= 0) {
      in_backlog = count;
    }
    // TODO(alex): co, kdyz ne?
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
    return port > 0;  // TODO(alex): detailnejsi kontrola?
  }
};

#endif  // SRC_PROXY_PROXYCONFIGURATION_H_
