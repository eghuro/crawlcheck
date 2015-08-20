// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HELPERROUTINES_H_
#define SRC_PROXY_HELPERROUTINES_H_

#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <string>
#include <sstream>

class HelperRoutines {
 public:
  /**
   * Print an error message and exit the application.
   * Message is printed via perror - message
   * @param message a message to print
   */
  static inline void error(const std::string & message) {
    std::ostringstream oss;
    oss << "[ERROR] (PID: "<<getpid()<<") "<< message;
    perror(oss.str().c_str());
    exit(EXIT_FAILURE);
  }

  static inline void error(const std::string & message, const std::string & err) {
    fprintf(stderr, "[ERROR] (PID: %d) %s: %s\n\n", getpid(), message.c_str(), err.c_str());
    exit(EXIT_FAILURE);
  }

  static inline void warning(const std::string & message) {
    std::ostringstream oss;
    oss << "[WARNING] (PID: "<<getpid()<<") "<< message;
    perror(oss.str().c_str());
  }

  static inline void warning(const std::string & message,
    const std::string & err) {
    fprintf(stderr, "[WARNING] (PID: %d) %s: %s\n\n", getpid(), message.c_str(), err.c_str());
  }

  static inline void info(const std::string & message) {
    fprintf(stdout, "[INFO] (PID: %d) %s\n", getpid(), message.c_str());
  }

  // https://stackoverflow.com/a/20861692/2561483
  template < typename T >
  static inline std::string to_string(const T& n) {
    std::ostringstream stm;
    stm << n;
    return stm.str();
  }

  static inline int toInt(const std::string & str) {
    return atoi(str.c_str());
  }
};

#endif  // SRC_PROXY_HELPERROUTINES_H_
