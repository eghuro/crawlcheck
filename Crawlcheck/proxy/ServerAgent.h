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

namespace crawlcheck {
namespace proxy {
class ServerAgent {
 public:
  explicit ServerAgent(int threadsCount);
  ~ServerAgent();

  // zatim zakazano:
  ServerAgent(const ServerAgent& other) = delete;  // copy constructor
  ServerAgent& operator= (const ServerAgent& other) = delete;  // copy assment
  ServerAgent& operator= (ServerAgent&& other) = delete;  // move assment optor

  bool threadsRunning();
  pthread_mutex_t* getThreadsRunningMutex();
  pthread_cond_t* getThreadsRunningCondition();
 private:
  pthread_mutex_t threadsRunningMutex;
  int thread_active;
  pthread_cond_t threadsRunningCondition;
  int thread_max;
  pthread_t * threads;
};
}  // namespace proxy
}  // namespace crawlcheck

#endif /* _NET_SERVERAGENT_H_ */  // NOLINT
