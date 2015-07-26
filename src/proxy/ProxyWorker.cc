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
#include "./ProxyConfiguration.h"
#include "./HelperRoutines.h"

ConnectionIdentifierFactory::identifier ConnectionIdentifierFactory::next = 0;
const int ProxyWorker::buffer_size = 1000;

void ProxyWorker::createThreads(void* parameter) {
  // vytvorit client thread
  int e = pthread_create(&client_thread, NULL, clientThreadRoutine,
    parameter);
  if (e != 0) {
    errx(1, "pthread_create (client): %s", strerror(e));
  } else {
    // povedlo se
    // vytvorit server thread
    e = pthread_create(&server_thread, NULL, serverThreadRoutine,
      parameter);
    if (e != 0) {
      // nepovedlo se
      errx(1, "pthread_create (server): %s", strerror(e));
      // zrusit client thread
      void *retval_client;
	  e = pthread_join(client_thread, &retval_client);
      if (e != 0) {
        errx(1, "pthread_join (client): %s", strerror(e));
      }
    }
  }
}

void ProxyWorker::startThread(int fd) {
    std::cout << fd << std::endl;
    ConnectionIdentifierFactory::identifier id = ConnectionIdentifierFactory::getId();
    ProxyWorker::parameter_type parameters(fd, request_storage, configuration, id);
    std::cout << std::get<1>(parameters) << std::endl;
    void * parameter = reinterpret_cast<void *>(&parameters);

    // vytvorit vlakna
	createThreads(parameter);
  }

void ProxyWorker::handleClientRequest(int new_fd,
		std::shared_ptr<RequestStorage> storage, ConnectionIdentifierFactory::identifier id) {
  HttpParser parser;
  char buf[ProxyWorker::buffer_size];
  int n;
  while ((n = read(new_fd, buf, ProxyWorker::buffer_size)) != 0) {
    if (n == -1) {
      perror("READ request");
    } else {
      HttpParserResult result = parser.parse(std::string(buf, n));
      if (result.isRequest()) {
        (*storage).insertParserResult(result, id);
      }
    }
  }
}

void ProxyWorker::handleClientResponse(int new_fd, std::shared_ptr<RequestStorage> storage, ConnectionIdentifierFactory::identifier id) {
  // RESPONSE
  while (!(*storage).done()) {
    if ((*storage).responseAvailable()) {
      std::string response = (*storage).retrieveResponse(id);
      write(new_fd, response.c_str(), response.size());
    }
  }
}

void* ProxyWorker::clientThreadRoutine(void * arg) {
  auto params = reinterpret_cast<ProxyWorker::parameter_type *>(arg);
  int fd = std::get<0>(*params);
  std::shared_ptr<RequestStorage> storage = std::get<1>(*params);
  auto id = std::get<3>(*params);

  int new_fd = accept(fd, NULL, NULL);
  if (new_fd == -1) {
    std::cout << fd <<std::endl;
    HelperRoutines::error("accept ERROR");
  }

  fprintf(stderr, ".. connection accepted ..\n");

  handleClientRequest(new_fd, storage, id);
  handleClientResponse(new_fd, storage, id);

  close(new_fd);
  fprintf(stderr, ".. connection closed ..\n");
  return NULL;
}

void* ProxyWorker::serverThreadRoutine(void * arg) {
  auto params = reinterpret_cast<ProxyWorker::parameter_type *>(arg);
  std::shared_ptr<RequestStorage> storage = std::get<1>(*params);
  std::shared_ptr<ProxyConfiguration> conf_ptr = std::get<2>(*params);

  auto ai = getAddrInfo(conf_ptr);
  auto sockets = getSockets(ai);

  int fd = *sockets.begin();

  // TODO(alex): ziskat struct sockaddr * pro adresu serveru, kam sel originalni request
  // connect(fd, addr, addrlen)
  int new_fd=-1;
  // write request
  if (storage -> requestAvailable()) {
	auto req_bundle = storage->retrieveRequest();
    std::string request = std::get<0>(req_bundle);
    int id = std::get<1>(req_bundle);

    write(fd, request.c_str(), request.size());

    // read response - opsat
    HttpParser parser;
    char buf[ProxyWorker::buffer_size];
    int n;
    while ((n = read(new_fd, buf, ProxyWorker::buffer_size)) != 0) {
      if (n == -1) {
        perror("READ response");
      } else {
        HttpParserResult result = parser.parse(std::string(buf, n));
        if (result.isResponse()) {
          (*storage).insertParserResult(result, id);
        }
      }
    }
  }

  for(auto it = sockets.begin(); it != sockets.end(); ++it) {
    close(*it);
  }
  return NULL;
}



ProxyWorker::~ProxyWorker() {
  void *retval_client, *retval_server;

  // zrusit client thread
  int e = pthread_join(client_thread, &retval_client);
  if (e != 0) {
  	errx(1, "pthread_join (client): %s", strerror (e));
  }

  // zrusit server thread
  e = pthread_join(server_thread, &retval_server);
  if (e != 0) {
    errx(1, "pthread_join (client): %s", strerror (e));
  }
}

