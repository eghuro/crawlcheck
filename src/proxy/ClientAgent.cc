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

pthread_mutex_t Bundle::stop_lock = PTHREAD_MUTEX_INITIALIZER;
bool Bundle::stop = false;

void * ClientThread::clientThreadRoutine(void * arg) {
  std::cout << "Client thread started" << std::endl;
  ClientThreadParameters * parameters = reinterpret_cast<ClientThreadParameters *>(arg);
  RequestStorage* storage = parameters->getStorage();

  // pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS,NULL);
  while (!Bundle::stop) {
    std::cout << "Working." << std::endl;
    // establish connection
    int connection = ClientThread::establishConnection(parameters);

    // handle request
    auto transactionIds = ClientThread::request(parameters, connection);

    // handle response
    ClientThread::response(transactionIds, connection, parameters);

    //close connection
    if (close(connection) != 0) HelperRoutines::warning("Close connection in client thread");
    else std::cout << ".. connection closed .. " << std::endl;
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

  ThreadedHelperRoutines::lock(mutex, "CAM");
  std::cout << "Waiting" << std::endl;
  while(!parameters->connectionAvailable()) {
    pthread_cond_wait(condition, mutex);
  }

  std::cout << "Connection is available" << std::endl;

  //accept
  ThreadedHelperRoutines::lock(parameters->getConnectionMutex(), "CM");
  std::cout << parameters->getConnection() << std::endl;
  int new_fd = accept(parameters->getConnection(), NULL, NULL); // checked after unlocks
  ThreadedHelperRoutines::unlock(parameters->getConnectionMutex(), "CM");
  ThreadedHelperRoutines::unlock(mutex, "CAM");
  std::cout << "Accpeted, unlocked" << std::endl;

  if (new_fd == -1) {
    HelperRoutines::warning("accept ERROR in client thread");
  }

  fprintf(stderr, ".. connection accepted ..\n");
  return new_fd;
  }

std::vector<std::size_t> ClientThread::request(ClientThreadParameters * parameters, int connection) {
  auto storage = parameters->getStorage();
    std::vector<std::size_t> transactionIds(1);
    //read request
    HttpParser parser;
    char buf[ClientThread::buffer_size];
    int n;

    while ((n = read(connection, buf, ClientThread::buffer_size)) != 0) {
      if (n == -1) {
        HelperRoutines::warning("Read request in client thread");
      } else {
        HttpParserResult result = parser.parse(std::string(buf, n));
        if (result.isRequest()) {
    //push DB
          ThreadedHelperRoutines::lock(parameters->getStorageLock(), "Storage lock");
          transactionIds.push_back((*storage).insertRequest(result));
          ThreadedHelperRoutines::unlock(parameters->getStorageLock(), "Storage lock");
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
  ThreadedHelperRoutines::lock(parameters->getStorageLock(), "Storage lock");
  storage->subscribeWait4Response(transactionIds[0], response_mutex, response_available);
  ThreadedHelperRoutines::unlock(parameters->getStorageLock(), "Storage lock");
  ThreadedHelperRoutines::lock(response_mutex, "Response mutex");
  while (!storage->responseAvailable(transactionIds[0])) {
    pthread_cond_wait(response_available, response_mutex);
  }
  ThreadedHelperRoutines::lock(parameters->getStorageLock(), "Storage lock");
  std::string response = storage->retrieveResponse(transactionIds[0]);
  ThreadedHelperRoutines::unlock(parameters->getStorageLock(), "Storage lock");
  ThreadedHelperRoutines::unlock(response_mutex, "Response mutex");

  //write response
  int n = write(static_cast<int>(connection), response.c_str(), response.size());
  if (n == -1) {
    HelperRoutines::warning("Write response in client thread");
  } else if (n != response.size()) {
    HelperRoutines::warning("Write response", "Bytes of response actually written in client thread don't match size of retrieved response");
  }
}
