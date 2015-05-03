/*
 * DownloaderThread.h
 * Copyright 2015 Alexandr Mansurov
 */

#ifndef CRAWLCHECK_NET_DOWNLOADERTHREAD_H_
#define CRAWLCHECK_NET_DOWNLOADERTHREAD_H_

#include <memory>
#include <string>
#include "./proxy.h"  // NOLINT

namespace crawlcheck {
namespace proxy {
class DownloaderThread {
 public:
  static void * work(void *);
 private:
  static std::string generateRequest(const crawlcheck::proxy::uri_t & uri);
  static void parseResponse(const std::ostringstream & response);
  static void poller(int fd);
  static uri_t getUri(AddressList * al);
};

} /* namespace proxy */
} /* namespace crawlcheck */
#endif  // CRAWLCHECK_NET_DOWNLOADERTHREAD_H_
