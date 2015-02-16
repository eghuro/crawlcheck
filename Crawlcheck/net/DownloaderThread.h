/*
 * DownloaderThread.h
 * Copyright 2015 Alexandr Mansurov
 */

#ifndef CRAWLCHECK_NET_DOWNLOADERTHREAD_H_
#define CRAWLCHECK_NET_DOWNLOADERTHREAD_H_

#include <memory>
#include "AddressList.h"

namespace crawlcheck {
namespace proxy {
class AddressList;
class DownloaderThread {
 public:
  static void * work(void *);
};

} /* namespace proxy */
} /* namespace crawlcheck */
#endif  // CRAWLCHECK_NET_DOWNLOADERTHREAD_H_
