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

  while (true) {
    // establish connection
    int connection = ClientThread::establishConnection(parameters);
    if (connection < 0) continue;

    // handle request
    auto transactionId = ClientThread::request(parameters, connection);

    std::cout << "Handle response, trid:" << transactionId << std::endl;
    // handle response
    ClientThread::response(transactionId, connection, parameters);

    //close connection
    if (close(connection) != 0) HelperRoutines::warning("Close connection in client thread");
    else std::cout << ".. connection closed .. " << std::endl;
  }
  delete parameters;
}

int ClientThread::establishConnection(ClientThreadParameters * parameters) {
  HelperRoutines::info("Establish connection");
  // wait for socket (for accept) to become available
 // pthread_mutex_t * mutex = parameters->getConnectionAvailabilityMutex();
  //pthread_cond_t * condition = parameters->getConnectionAvailabilityCondition();
  //assert (mutex != nullptr);
  //assert (condition != nullptr);

  //ThreadedHelperRoutines::lock(mutex, "CAM");
  HelperRoutines::info("Waiting");
  wait4connection(parameters);

  HelperRoutines::info("Connection is available");

  HelperRoutines::info(HelperRoutines::to_string(parameters->getConnection()));

  //accept
  ThreadedHelperRoutines::lock(parameters->getConnectionMutex(), "CM");
  std::cout << parameters->getConnection() << std::endl;
  int new_fd = accept(parameters->getConnection(), NULL, NULL); // checked after unlocks
  ThreadedHelperRoutines::unlock(parameters->getConnectionMutex(), "CM");
  //ThreadedHelperRoutines::unlock(mutex, "CAM");
  HelperRoutines::info("Accepted");

  if (new_fd == -1) {
    HelperRoutines::warning("accept ERROR in client thread");
  }

  fprintf(stderr, ".. connection accepted ..\n");
  return new_fd;
  }

std::size_t ClientThread::request(ClientThreadParameters * parameters, int connection) {
  HelperRoutines::info("Read request");
  HelperRoutines::info(HelperRoutines::to_string(connection));
  auto storage = parameters->getStorage();
    //std::vector<std::size_t> transactionIds(1);
    std::size_t transactionId;
    //read request
    HttpParser parser;
    char buf[ClientThread::in_buffer_size];
    int n;
    bool readFailed = false;

    std::stringstream sst;
    while ((n = read(connection, buf, ClientThread::in_buffer_size)) != 0 && !readFailed) {
      if (n == -1) {
        readFailed = true;
        HelperRoutines::warning("Read request in client thread");
      } else {
        sst << buf;
        if (n < ClientThread::in_buffer_size) {
          break;
        }
      }
    }

    if (!readFailed) {
      std::cout << sst.str() << std::endl;
      HttpParserResult result = parser.parse(sst.str());
      if (result.isRequest()) {
  //push DB
        ThreadedHelperRoutines::lock(parameters->getStorageLock(), "Storage lock");
        transactionId = (*storage).insertRequest(result);
        ThreadedHelperRoutines::unlock(parameters->getStorageLock(), "Storage lock");
      }
    }

    HelperRoutines::info("Read request end");
    return transactionId;
  }

void ClientThread::response(const std::size_t & transactionId, int connection, ClientThreadParameters * parameters) {
  HelperRoutines::info("Write response");
  auto storage = parameters->getStorage();
  //wait for response
  //pthread_mutex_t * response_mutex = parameters->getResponseAvailabilityMutex();
  //pthread_cond_t * response_available = parameters->getResponseAvailabilityCondition();
  //ThreadedHelperRoutines::lock(parameters->getStorageLock(), "Storage lock");
  //storage->subscribeWait4Response(transactionIds[0], response_mutex, response_available);
  //ThreadedHelperRoutines::unlock(parameters->getStorageLock(), "Storage lock");

  //ThreadedHelperRoutines::lock(response_mutex, "Response mutex");
  wait4response(storage, transactionId);//pozor, storage neni zamknuta a je sdilane
  ThreadedHelperRoutines::lock(parameters->getStorageLock(), "Storage lock");
  std::string response = storage->retrieveResponse(transactionId);
  ThreadedHelperRoutines::unlock(parameters->getStorageLock(), "Storage lock");
  //ThreadedHelperRoutines::unlock(response_mutex, "Response mutex");

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
