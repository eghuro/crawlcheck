// Copyright 2015 Alexandr Mansurov

#include "./ProxyWorker.h"
#include <string>
#include <memory>
#include <stdio.h>
#include <sys/socket.h>
#include <unistd.h>
#include "./HttpParser.h"
#include "./RequestStorage.h"

const int ProxyWorker::buffer_size = 1000;
const std::unique_ptr<RequestStorage> request_storage = std::unique_ptr<RequestStorage>(new RequestStorage());

void* ProxyWorker::clientThreadRoutine(void * arg) {
  int fd = reinterpret_cast<int>(arg); //TODO(alex): arg ~> std::pair<int, std::unique_ptr<RequestStorage>>

  int new_fd = accept(fd, NULL, NULL);
  if (new_fd == -1) {
    HelperRoutines::error("accept ERROR");
  }

  char buf[ProxyWorker::buffer_size];
  fprintf(stderr, ".. connection accepted ..\n");

  HttpParser parser;

  int n;
  while ((n = read(new_fd, buf, ProxyWorker::buffer_size)) != 0) {
    if (n == -1) {
      perror("READ");
    } else {
      HttpParserResult result = parser.parse(std::string(buf, n));
      write(1, buf, n);

      if (result.request()) {
    	 // (*ProxyWorker::request_storage).insertParserResult(result);
      }
    }
  }

  // TODO (alex): poslouchat, zda neni pripravena response, ve vhodny okamzik odeslat response

  close(new_fd);
  fprintf(stderr, ".. connection closed ..\n");
  return NULL;
}

void* ProxyWorker::serverThreadRoutine(void * arg) {
  return NULL;
}

