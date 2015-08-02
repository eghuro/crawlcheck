// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HELPERROUTINES_H_
#define SRC_PROXY_HELPERROUTINES_H_

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
    perror(message.c_str());
    exit(EXIT_FAILURE);
  }

  static inline void warning(const std::string & message) {
    perror(message.c_str());
  }

  static inline void warning(const std::string & message, const std::string & err) {
    fprintf(stderr, "%s: %s\n\n", message.c_str(), err.c_str());
  }

  // https://stackoverflow.com/a/20861692/2561483
  template < typename T >
  static std::string to_string(const T& n) {
    std::ostringstream stm;
    stm << n;
    return stm.str();
  }
};

#endif  // SRC_PROXY_HELPERROUTINES_H_
