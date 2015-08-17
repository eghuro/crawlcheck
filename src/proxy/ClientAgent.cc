// Copyright 2015 Alexandr Mansurov
#include "ClientAgent.h"
#include <unistd.h>
#include <stdio.h>
#include <pthread.h>
#include <sys/socket.h>
#include <memory>
#include "./RequestStorage.h"
#include "./HttpParser.h"

std::size_t ClientThread::buffer_size = 1000;

void * ClientThread::clientThreadRoutine(void * arg) {
  ClientWorkerParameters * parameters = reinterpret_cast<ClientWorkerParameters *>(arg);
  std::shared_ptr<RequestStorage> storage = parameters->getStorage();

  while (parameters->doWork()) {
    // establish connection
    int connection = ClientThread::establishConnection(parameters);

    // handle request
    auto transactionIds = ClientThread::request(parameters, connection);

    // handle response
    ClientThread::response(transactionIds, connection, parameters);

    //close connection
    close(connection);
    fprintf(stderr, ".. connection closed ..\n");
  }
}

int ClientThread::establishConnection(ClientWorkerParameters * parameters) {
    // wait for socket (for accept) to become available
    pthread_mutex_t * mutex = parameters->getConnectionAvailabilityMutex();
    pthread_cond_t * condition = parameters->getConnectionAvailabilityCondition();
    pthread_mutex_lock(mutex);
    while(!parameters->connectionAvailable()) {
      pthread_cond_wait(condition, mutex);
    }

    //accept
    int new_fd = accept(parameters->getConnection(), NULL, NULL);
    pthread_mutex_unlock(mutex);

    if (new_fd == -1) {
      HelperRoutines::error("accept ERROR");
    }

    fprintf(stderr, ".. connection accepted ..\n");
    return new_fd;
  }

std::vector<std::size_t> ClientThread::request(const ClientWorkerParameters * parameters, int connection) {
  auto storage = parameters->getStorage();
    std::vector<std::size_t> transactionIds(1);
    //read request
    HttpParser parser;
    char buf[ClientThread::buffer_size];
    int n;

    while ((n = read(connection, buf, ClientThread::buffer_size)) != 0) {
      if (n == -1) {
        perror("READ request");
      } else {
        HttpParserResult result = parser.parse(std::string(buf, n));
        if (result.isRequest()) {
    //push DB
          transactionIds.push_back((*storage).insertRequest(result));
        }
      }
    }

    return transactionIds;
  }

void ClientThread::response(const std::vector<std::size_t> & transactionIds, int connection, ClientWorkerParameters * parameters) {
  auto storage = parameters->getStorage();
  //wait for response
  pthread_mutex_t * response_mutex = parameters->getResponseAvailabilityMutex();
  pthread_cond_t * response_available = parameters->getResponseAvailabilityCondition();
  storage->subscribeWait4Response(transactionIds[0], response_mutex, response_available);
  pthread_mutex_lock(response_mutex);
  while (!storage->responseAvailable(transactionIds[0])) {
    pthread_cond_wait(response_available, response_mutex);
  }
  std::string response = storage->retrieveResponse(transactionIds[0]);
  pthread_mutex_unlock(response_mutex);

  //write response
  write(static_cast<int>(connection), response.c_str(), response.size());
}
