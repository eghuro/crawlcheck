// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_PROXYCONFIGURATION_H_
#define SRC_PROXY_PROXYCONFIGURATION_H_

#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include "./HelperRoutines.h"

/**
 * ProxyConfiguration holds configuration for a Proxy object.
 * A separate object was chosen to prevent passing big amount of parameters
 * around.
 *
 * The ProxyConfiguration is composed of "setters" and "getters" for various
 * options. Setters do input verification and return bool - true if the value
 * was successfully changed or false if the input was not valid.
 */
class ProxyConfiguration {
 public:
  /**
   * Constructor sets values to "safely invalid". Everything must be set
   * manually using setters.
   */
  ProxyConfiguration():in_pool_count(0),  max_in(0), max_out(0),
    in_pool_port(-1), dbc_fd(-1), in_backlog(-1) {}
  virtual ~ProxyConfiguration() {}

  // TODO(alex): not in use
  inline bool setPoolCount(int count) {
    if (count >= 0) {
      in_pool_count = count;
      return true;
    }
    return false;
  }

  // TODO(alex): not in use
  inline bool setMaxIn(int max) {
    if (max >= 0) {
      max_in = max;
      return true;
    }
    return false;
  }

  // TODO(alex): not in use
  inline bool setMaxOut(int max) {
    if (max >= 0) {
      max_out = max;
      return true;
    }
    return false;
  }

  /**
   * Port to listen for incoming connections at.
   * @param port port is greater or equal to 1 and less or equal to 65535
   * @return if the port was acceptable and the value therefore changed or not
   */
  inline bool setInPoolPort(int port) {
    if (acceptablePort(port)) {
      in_pool_port = port;
      return true;
    }
    return false;
  }

  // TODO(alex): not in use
  inline bool setDbcFd(int fd) {
    if (fd >= 0) {
      dbc_fd = fd;
      return true;
    } else {
      return false;
    }
  }

  /**
   * Sets backlog for listening for connections.
   *
   * The backlog argument provides a hint to the  implementation  which  the
   * implementation shall use to limit the number of outstanding connections
   * in the socket's listen queue. Implementations may  impose  a  limit  on
   * backlog  and  silently  reduce  the specified value. Normally, a larger
   * backlog argument value shall result in a larger or equal length of  the
   * listen  queue.  Implementations  shall  support values of backlog up to
   * SOMAXCONN, defined in <sys/socket.h>.
   *
   * @param count backlog's count, must be greater or equal to 0, count greater
   * than SOMAXCONN is silently reduced to SOMAXCONN
   * @return true if count was greater or equal then 0, false otherwise, value
   * is changed internally only when "true" is returned.
   */
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

  // TODO(alex): not in use
  inline int getPoolCount() const {
    return in_pool_count;
  }

  // TODO(alex): not in use
  inline int getMaxIn() const {
    return max_in;
  }

  // TODO(alex): not in use
  inline int getMaxOut() const {
    return max_out;
  }

  /**
   * Incoming port.
   * @return The port to listen for incoming connections at.
   */
  inline int getInPoolPort() const {
    return in_pool_port;
  }

  // TODO(alex): not in use
  inline int getDbcFd() const {
    return dbc_fd;
  }

  /**
   * Backlog for listening to connections.
   * @return backlog
   */
  inline int getInBacklog() const {
    return in_backlog;
  }

  /**
   * Get string representation of incoming port.
   * @return The port to listen for incoming connections at as string.
   */
  inline std::string getInPortString() const {
    return HelperRoutines::to_string(in_pool_port);
  }

 private:
  int in_pool_count;
  int max_in, max_out;
  int in_pool_port;
  int dbc_fd;
  int in_backlog;

  static const int minPort, maxPort;

  inline bool acceptablePort(int port) {
    return (port >= minPort) && (port <= maxPort);
  }
};

#endif  // SRC_PROXY_PROXYCONFIGURATION_H_
