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

#include "DownloaderThread.h"
#include "AddressList.h"

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
  // bud potrebuji druhou metodu - podminka ukonceni cyklu - nebo se aplikace ukoncuje zabitim

  while (runCondition) {
    // uri from address list
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

    // getaddrinfo
    struct addrinfo * addr;
    if (getaddrinfo(uri.addr.c_str(), uri.port.c_str(), &hints, &addr) != 0) {
      std::cout << "Failed to resolve" << uri.addr << std::endl;
    } else {
      // socket
      struct addrinfo *res;
      for (res = addr; res != NULL; res=res->ai_next) {
        int fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
        if (fd != -1) {
          // connect
          if (connect(fd, (struct sockaddr *)res->ai_addr, res->ai_addrlen)
            == 0) {
            // write
        	std::cout << "Generate request" << std::endl;
            std::string request = generateRequest(uri);
            const char * msg = request.c_str();
            if (write(fd, msg, sizeof (msg)) == -1) {
              std::cout << "Write error" << std::endl;
            } else {
              // poll
              struct pollfd pfd[1];
              pfd[0].fd = fd;
              pfd[0].events = POLLIN | POLLPRI;
              const int BUFSIZE = 255;
              const int TIMEOUT = 60000;
              char buffer[BUFSIZE];
              if (poll(pfd, 1, TIMEOUT) > 0) {
                // read
                std::cout<<std::endl<<"Printout"<<std::endl<<std::endl;
                char *bufptr = buffer;
                while (read(fd, bufptr, BUFSIZE) > 0) {
                  bufptr = buffer;
                  std::cout << buffer << std::endl;
                }
                bufptr = buffer;
                std::cout << buffer << std::endl;
                // TODO(alex): HTTP Response se vytvori a preda pryc nekde zde
              }
            }
          }
          close(fd);
        }
      }
    }
  }
  return nullptr;
}

std::string DownloaderThread::generateRequest(const uri_t & uri) {
  return "GET " + (uri.page != "" ? uri.page : "/")+"\n";
}
