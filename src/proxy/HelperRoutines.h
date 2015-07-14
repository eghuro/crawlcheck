// Copyright 2015 Alexandr Mansurov

#ifndef SRC_PROXY_HELPERROUTINES_H_
#define SRC_PROXY_HELPERROUTINES_H_

#include <string>

class HelperRoutines {
 public:
  static void error(const std::string & message) {
    perror(message.c_str());
    exit(EXIT_FAILURE);
  }
};

#endif  // SRC_PROXY_HELPERROUTINES_H_
