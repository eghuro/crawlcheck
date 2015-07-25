// Copyright 2015 Alexandr Mansurov

#include "./ProxyWorker.h"
#include <string>
#include <memory>
#include <utility>
#include <stdio.h>
#include <sys/socket.h>
#include <unistd.h>
#include "./HttpParser.h"
#include "./RequestStorage.h"

const int ProxyWorker::buffer_size = 1000;

void* ProxyWorker::clientThreadRoutine(void * arg) {
  auto params = reinterpret_cast<std::pair<int, std::shared_ptr<RequestStorage>> *>(arg);
  int fd = params->first;
  std::shared_ptr<RequestStorage> storage = params->second;

  int new_fd = accept(fd, NULL, NULL);
  if (new_fd == -1) {
    std::cout << fd <<std::endl;
    HelperRoutines::error("accept ERROR");
  }

  char buf[ProxyWorker::buffer_size];
  fprintf(stderr, ".. connection accepted ..\n");

  HttpParser parser;

  // REQUEST
  int n;
  while ((n = read(new_fd, buf, ProxyWorker::buffer_size)) != 0) {
    if (n == -1) {
      perror("READ");
    } else {
      HttpParserResult result = parser.parse(std::string(buf, n));

      if (result.request()) {
        (*storage).insertParserResult(result);
      }

      if ((*storage).responseAvailable()) {
	    std::string response = (*storage).retrieveResponse();
	    write(new_fd, response.c_str(), response.size());
      }
    }
  }

  // RESPONSE
  while (!(*storage).done()) {
    if ((*storage).responseAvailable()) {
	  std::string response = (*storage).retrieveResponse();
	  write(new_fd, response.c_str(), response.size());
    }
  }

  close(new_fd);
  fprintf(stderr, ".. connection closed ..\n");
  return NULL;
}

void* ProxyWorker::serverThreadRoutine(void * arg) {
  return NULL;
}

