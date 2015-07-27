// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HELPERROUTINES_H_
#define SRC_PROXY_HELPERROUTINES_H_

#include <string>
#include <sstream>

class HelperRoutines {
 public:
  static inline void error(const std::string & message) {
    perror(message.c_str());
    exit(EXIT_FAILURE);
  }

  static inline void warning(const std::string & message) {
    perror(message.c_str());
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
