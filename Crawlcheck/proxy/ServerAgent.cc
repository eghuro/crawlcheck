/*
 * ServerAgent.cc
 * Copyright 2015 Alexandr Mansurov
 *
 * N threads are downloading list of addresses (which is common for all of the
 * threads and might be modified over the time)
 * Each thread is downloading at most one address at same time
 */

#include <pthread.h>
#include "./ServerAgent.h"  // NOLINT

using crawlcheck::proxy::ServerAgent;

ServerAgent::ServerAgent(int threadsCount):
  threadsRunningMutex(PTHREAD_MUTEX_INITIALIZER), thread_active(0),
  threadsRunningCondition(PTHREAD_COND_INITIALIZER), thread_max(threadsCount) {
  threads = new pthread_t[threadsCount];
}

ServerAgent::~ServerAgent() {
  delete threads;
}

bool ServerAgent::threadsRunning() {
  return thread_active > 0;
}

pthread_mutex_t* ServerAgent::getThreadsRunningMutex() {
  return &threadsRunningMutex;
}

pthread_cond_t* ServerAgent::getThreadsRunningCondition() {
  return &threadsRunningCondition;
}
