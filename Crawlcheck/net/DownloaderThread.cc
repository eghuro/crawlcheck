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

void * DownloaderThread::work(void * foo) {
  AddressList * al = reinterpret_cast<AddressList *>(foo);

  struct addrinfo hints;
  memset(&hints, 0, sizeof (hints));
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_STREAM;

  bool runCondition = true;
  // TODO(alex): potrebuji druhou metodu - podminka ukonceni cyklu

  while (runCondition) {
    printf("Get mutex on address list\n");
    pthread_mutex_lock((*al).getMutex());
    while (!(*al).getURIavailable()) {
      printf("Wait for address\n");
      pthread_cond_wait((*al).getCondition(), (*al).getMutex());
    }
    crawlcheck::proxy::uri_t uri = (*al).getURI();
    // printf("%s\n",&uri);
    std::cout << uri << std::endl;
    pthread_mutex_unlock((*al).getMutex());
    printf("Release mutex on address list\n");

    // getaddrinfo
    // socket
    // connect
    // write
    // poll
    // read

    runCondition = false;
  }



  // TODO(alex): downloading
  printf("Hello\n");
  sleep(3);
  printf("Goodbye\n");



  return nullptr;
}
