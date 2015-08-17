// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_PROXYCONFIGURATION_H_
#define SRC_PROXY_PROXYCONFIGURATION_H_

#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <sstream>
#include <libxml++/libxml++.h>
#include <glibmm/convert.h>
#include "./HelperRoutines.h"
#include "./db.h"

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
  ProxyConfiguration():in_pool_count(0), in_pool_port(-1), in_backlog(-1) {}
  virtual ~ProxyConfiguration() {}

  void setInPoolCount(std::size_t count) {
    in_pool_count = static_cast<int>(count);
  }

  int getInPoolCount() const {
    return in_pool_count;
  }

  void setOutPoolCount(std::size_t count) {
    out_pool_count = static_cast<int>(count);
  }

  int getOutPoolCount() const {
    return out_pool_count;
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

  /**
   * Backlog for listening to connections.
   * @return backlog
   */
  inline int getInBacklog() const {
    return in_backlog;
  }

  /**
   * Incoming port.
   * @return The port to listen for incoming connections at.
   */
  inline int getInPoolPort() const {
    return in_pool_port;
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

  /**
   * Get string representation of incoming port.
   * @return The port to listen for incoming connections at as string.
   */
  inline std::string getInPortString() const {
    return HelperRoutines::to_string(in_pool_port);
  }

 private:
  int in_pool_count;
  int in_pool_port;
  int in_backlog;
  int out_pool_count;

  static const int minPort, maxPort;

  inline bool acceptablePort(int port) {
    return (port >= minPort) && (port <= maxPort);
  }
};

class ConfigurationParser : public xmlpp::SaxParser {
 public:
  ConfigurationParser(): versionMatches(false) {}
  virtual ~ConfigurationParser() {}

  const ProxyConfiguration & getProxyConfiguration() const {
    return pconf;
  }

  const DatabaseConfiguration & getDatabaseConfiguration() const {
    return dconf;
  }

  bool versionMatch() const {
    return versionMatches;
  }

 protected:
  virtual void on_start_document() {
    versionMatches = false;
  }

  virtual void on_start_element(const Glib::ustring& name,
                                const AttributeList& properties) {
    if (name == "crawlcheck") {
      for (auto it = properties.begin(); it != properties.end(); ++it) {
        try {
          if (it->name == "version") {
            versionMatches = (it->value == ConfigurationParser::version);
          }
        } catch (const Glib::ConvertError& ex) {
          std::ostringstream oss;
          oss << "Parsing configuration version: " << ex.what();
          HelperRoutines::error(oss.str());
        }
      }
    } else if (name == "db") {
      for (auto it = properties.begin(); it != properties.end(); ++it) {
        try {
          if (it->name == "user") {
            dconf.setUser(it->value);
          } else if (it->name == "pass") {
             dconf.setPass(it->value);
          } else if (it->name == "uri") {
            dconf.setUri(it->value);
          } else if (it->name == "dbname") {
            dconf.setDb(it->value);
          }
        } catch (const Glib::ConvertError& ex) {
          std::ostringstream oss;
          oss << "Parsing DB configuration: " << ex.what();
          HelperRoutines::error(oss.str());
        }
      }
    } else if (name == "proxy") {
      for (auto it = properties.begin(); it != properties.end(); ++it) {
        try {
          if (it->name =="inPool") {
            pconf.setInPoolCount(static_cast<std::size_t>(HelperRoutines::toInt(it->value)));
          } else if (it->name == "outPool") {
            pconf.setOutPoolCount(static_cast<std::size_t>(HelperRoutines::toInt(it->value)));
          } else if (it->name == "inPort") {
            pconf.setInPoolPort(HelperRoutines::toInt(it->value));
          } else if (it->name == "inBacklog") {
            pconf.setInBacklog(HelperRoutines::toInt(it->value));
          }
        } catch (const Glib::ConvertError& ex) {
          std::ostringstream oss;
          oss << "Parsing DB configuration: " << ex.what();
          HelperRoutines::error(oss.str());
        }
      }
    }
  }

  virtual void on_end_document() {}
  virtual void on_end_element(const Glib::ustring& name) {}
  virtual void on_characters(const Glib::ustring& characters) {}
  virtual void on_comment(const Glib::ustring& text) {}
  virtual void on_warning(const Glib::ustring& text) {}
  virtual void on_error(const Glib::ustring& text) {}
  virtual void on_fatal_error(const Glib::ustring& text) {}

 private:
  bool versionMatches;
  ProxyConfiguration pconf;
  DatabaseConfiguration dconf;

  static const std::string version;
};

#endif  // SRC_PROXY_PROXYCONFIGURATION_H_
