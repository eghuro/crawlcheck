/*
 * ServerAgent.h
 * Copyright 2015 Alexandr Mansurov
 *
 * N threads are downloading list of addresses (which is common for all of the
 * threads and might be modified over the time)
 * Each thread is downloading at most one address at same time
 */

#ifndef _NET_SERVERAGENT_H_  // NOLINT
#define _NET_SERVERAGENT_H_  // NOLINT

#include <pthread.h>
#include <memory>
#include "./DownloaderThread.h"  // NOLINT
#include "./AddressList.h"

namespace crawlcheck {
namespace proxy {
class AddressList;

class ServerAgent {
 public:
  ServerAgent();
  explicit ServerAgent(int threadsCount);
  virtual ~ServerAgent();

  // zatim zakazano:
  ServerAgent(const ServerAgent& other) = delete;  // copy constructor
  ServerAgent& operator= (const ServerAgent& other) = delete;  // copy assment
  ServerAgent& operator= (ServerAgent&& other) = delete;  // move assment optor

  bool threadsRunning();
  pthread_mutex_t* getThreadsRunningMutex();
  pthread_cond_t* getThreadsRunningCondition();

  void setAddressList(crawlcheck::proxy::AddressList *);
  void run();

 private:
  pthread_mutex_t threadsRunningMutex;
  int thread_active;
  pthread_cond_t threadsRunningCondition;
  int thread_max;
  pthread_t * threads;
  std::unique_ptr< crawlcheck::proxy::DownloaderThread > * downloaders;
  crawlcheck::proxy::AddressList * addrListPtr;
};
}  // namespace proxy
}  // namespace crawlcheck

#endif /* _NET_SERVERAGENT_H_ */  // NOLINT
