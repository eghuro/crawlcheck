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
  std::cout << "Client thread started" << std::endl;
  ClientThreadParameters * parameters = reinterpret_cast<ClientThreadParameters *>(arg);
  std::shared_ptr<RequestStorage> storage = parameters->getStorage();

  std::cout << "Do work?" << parameters->doWork() << std::endl;
  pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS,NULL);
  while (parameters->doWork()) {
    std::cout << "Working." << std::endl;
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
  delete parameters;
}

int ClientThread::establishConnection(ClientThreadParameters * parameters) {
  std::cout << "Establish connection" << std::endl;
  // wait for socket (for accept) to become available
  pthread_mutex_t * mutex = parameters->getConnectionAvailabilityMutex();
  pthread_cond_t * condition = parameters->getConnectionAvailabilityCondition();
  assert (mutex != nullptr);
  assert (condition != nullptr);

  pthread_mutex_lock(mutex);
  std::cout << "Waiting" << std::endl;
  while(!parameters->connectionAvailable()) {
    pthread_cond_wait(condition, mutex);
  }

  std::cout << "Connection is available" << std::endl;

  //accept
  pthread_mutex_lock(parameters->getConnectionMutex());
  std::cout << parameters->getConnection() << std::endl;
  int new_fd = accept(parameters->getConnection(), NULL, NULL);
  pthread_mutex_unlock(parameters->getConnectionMutex());
  pthread_mutex_unlock(mutex);
  std::cout << "Accpeted, unlocked" << std::endl;

  if (new_fd == -1) {
    HelperRoutines::error("accept ERROR");
  }

  fprintf(stderr, ".. connection accepted ..\n");
  return new_fd;
  }

std::vector<std::size_t> ClientThread::request(const ClientThreadParameters * parameters, int connection) {
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

void ClientThread::response(const std::vector<std::size_t> & transactionIds, int connection, ClientThreadParameters * parameters) {
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
