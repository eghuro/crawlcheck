// Copyright 2015 Alexandr Mansurov
#include "ClientAgent.h"
#include <unistd.h>
#include <stdio.h>
#include <pthread.h>
#include <sys/socket.h>
#include <memory>
#include "./RequestStorage.h"
#include "./HttpParser.h"

std::size_t ClientThread::in_buffer_size = 1000;
std::size_t ClientThread::out_buffer_size = 1000;

pthread_mutex_t Bundle::stop_lock = PTHREAD_MUTEX_INITIALIZER;
bool Bundle::stop = false;

void * ClientThread::clientThreadRoutine(void * arg) {
  std::cout << "Client thread started" << std::endl;
  ClientThreadParameters * parameters = reinterpret_cast<ClientThreadParameters *>(arg);
  std::cout << parameters << std::endl;
  RequestStorage* storage = parameters->getStorage();

  // pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS,NULL);
  while (true) {
    // establish connection
    int connection = ClientThread::establishConnection(parameters);
    if (connection < 0) continue;

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
  HelperRoutines::info("Establish connection");
  // wait for socket (for accept) to become available
  pthread_mutex_t * mutex = parameters->getConnectionAvailabilityMutex();
  pthread_cond_t * condition = parameters->getConnectionAvailabilityCondition();
  assert (mutex != nullptr);
  assert (condition != nullptr);

  ThreadedHelperRoutines::lock(mutex, "CAM");
  HelperRoutines::info("Waiting");
  while(!parameters->connectionAvailable()) {
    pthread_cond_wait(condition, mutex);
  }

  HelperRoutines::info("Connection is available");

  HelperRoutines::info(HelperRoutines::to_string(parameters->getConnection()));

  //accept
  ThreadedHelperRoutines::lock(parameters->getConnectionMutex(), "CM");
  std::cout << parameters->getConnection() << std::endl;
  int new_fd = accept(parameters->getConnection(), NULL, NULL); // checked after unlocks
  ThreadedHelperRoutines::unlock(parameters->getConnectionMutex(), "CM");
  ThreadedHelperRoutines::unlock(mutex, "CAM");
  HelperRoutines::info("Accepted");

  if (new_fd == -1) {
    HelperRoutines::warning("accept ERROR in client thread");
  }

  fprintf(stderr, ".. connection accepted ..\n");
  return new_fd;
  }

std::vector<std::size_t> ClientThread::request(ClientThreadParameters * parameters, int connection) {
  HelperRoutines::info("Read request");
  HelperRoutines::info(HelperRoutines::to_string(connection));
  auto storage = parameters->getStorage();
    std::vector<std::size_t> transactionIds(1);
    //read request
    HttpParser parser;
    char buf[ClientThread::in_buffer_size];
    int n;
    bool readFailed = false;

    while ((n = read(connection, buf, ClientThread::in_buffer_size)) != 0 && !readFailed) {
      if (n == -1) {
        readFailed = true;
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
  HelperRoutines::info("Write response");
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
  const char * data = response.c_str();
  const std::size_t size = strlen(data);
  const char * buf_ptr = data;
  int n, sum = 0;
  bool writeFailed = false;

  // write request
  while ((sum < size) && !writeFailed) {
    n = write(connection, buf_ptr+sum, ClientThread::out_buffer_size);
    if (n == -1) { HelperRoutines::warning("Write response"); writeFailed = true; }
    else if (n > 0) {
      sum += n;
    }
  }
}
