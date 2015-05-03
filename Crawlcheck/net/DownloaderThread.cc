/*
 * DownloaderThread.cpp
 * Copyright 2015 Alexandr Mansurov
 *
 * Actual downloading done here
 */

#include <pthread.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <poll.h>

#include <iostream>
#include <sstream>
#include <string>

#include "DownloaderThread.h"
#include "AddressList.h"
#include "message.h"

using crawlcheck::proxy::DownloaderThread;
using crawlcheck::proxy::AddressList;
using crawlcheck::proxy::uri_t;

void * DownloaderThread::work(void * foo) {
  AddressList * al = reinterpret_cast<AddressList *>(foo);

  struct addrinfo hints;
  memset(&hints, 0, sizeof (hints));
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_STREAM;

  bool runCondition = true;
  // bud potrebuji druhou metodu - podminka ukonceni cyklu
  // nebo se aplikace ukoncuje zabitim

  while (runCondition) {
    // uri from address list
    uri_t uri = getUri(al);

    // getaddrinfo
    struct addrinfo * addr;
    if (getaddrinfo(uri.addr.c_str(), uri.port.c_str(), &hints, &addr) != 0) {
      std::cout << "Failed to resolve" << uri.addr << std::endl;
    } else {
      // socket
      struct addrinfo *res;
      for (res = addr; res != NULL; res=res->ai_next) {  // one hostname can
        // map to multiple addresses
        if (res->ai_family != AF_INET && res->ai_family != AF_INET6)
          continue;
        int fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
        if (fd != -1) {
          // connect
          if (connect(fd, (struct sockaddr *)res->ai_addr, res->ai_addrlen)
            == 0) {
            // write
            std::cout << "Generate request" << std::endl;
            std::string request = generateRequest(uri);
            std::cout << request << std::endl;
            const char * msg = request.c_str();
            if (write(fd, msg, strlen(msg)) == -1) {
              std::cout << "Write error" << std::endl;
            } else {
              poller(fd);
            }
          }
          close(fd);
          break;
        }
      }
      freeaddrinfo(addr);
    }
  }
  return nullptr;
}

std::string DownloaderThread::generateRequest(const uri_t & uri) {
  return "GET " +
    (uri.page == "" ? "/" : ("/"+uri.page)) +
    " HTTP/1.1\n"+
    "Host: "+uri.addr+
    "\n\n\0";
}

void DownloaderThread::parseResponse(const std::ostringstream & response) {
  // TODO(alex): HTTP Response se vytvori a preda pryc zde
  std::cout << response.str();

  int status;
  std::string content-type;
  std::string content;
  /*
   * HTTP/1.1 200 OK
   * Date: Fri, 20 Feb 2015 07:53:56 GMT
   * Server: Apache/2.2.29 (FreeBSD) mod_ssl/2.2.29 OpenSSL/0.9.8za-freebsd DAV/2
   * Accept-Ranges: bytes
   * Transfer-Encoding: chunked
   * Content-Type: text/html
   *
   * 1c0
   * <!DOCTYPE html>
   * <head>
   */

  // TODO(alex): zmena - zde se rovnou zahackuje dispatcher validatoru
  /*
   * motivace - uz mame pool vlaken, validace bezi take paralelne,
   * usetrime si namahu "vse nalit do uzkeho hrdla a pak znovu do vlaken"
   * data se budou vyhazovat do autonomniho reportu
   * crawler je take autonomni a cpe data do addresslistu
   */
}

void DownloaderThread::poller(int fd) {
  // poll
  std::cout << "Polling" << std::endl;

  struct pollfd pfd[1];
  pfd[0].fd = fd;
  pfd[0].events = POLLIN | POLLPRI;

  const int BUFSIZE = 10000;
  const int TIMEOUT = 60000;
  char buffer[BUFSIZE];

  if (poll(pfd, 1, TIMEOUT) > 0) {
    // read
    std::cout << std::endl << "Printout" << std::endl << std::endl;
    char *bufptr = buffer;
    int x, count = 0;
    std::ostringstream result;

    while ((x = read(fd, bufptr, BUFSIZE)) > 0) {
      result << buffer;
      count+=x;
    }
    std::cout << count << std::endl;
    parseResponse(result);
  } else {
    std::cout << "Timeout" <<std::endl;
  }
}

uri_t DownloaderThread::getUri(AddressList * al) {
  std::cout << "Get mutex on address list" << std::endl;
  pthread_mutex_lock((*al).getMutex());
  while (!(*al).getURIavailable()) {
    std::cout << "Wait for address" << std::endl;
    pthread_cond_wait((*al).getAvailableCondition(), (*al).getMutex());
  }
  uri_t uri = (*al).getURI();
  std::cout << "Got: " << uri.addr << ":" << uri.port << std::endl;
  pthread_mutex_unlock((*al).getMutex());
  std::cout << "Release mutex on address list" << std::endl;
  return uri;
}
