/*
 * proxy.h
 * Copyright 2015 Alexandr Mansurov
 *
 *  Created on: 17 Feb 2015
 *      Author: alex
 */

#ifndef CRAWLCHECK_NET_PROXY_H_
#define CRAWLCHECK_NET_PROXY_H_

#include <string>
namespace crawlcheck {
namespace proxy {
struct uri_t {
  std::string port;
  std::string addr;
  std::string page;
};

class ServerAgent;
class AddressList;
class DownloaderThread;
}  // namespace proxy
}  // namespace crawlcheck


#endif  // CRAWLCHECK_NET_PROXY_H_
