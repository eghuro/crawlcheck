/*
 * ServerAgent.cc
 * Copyright 2015 Alexandr Mansurov
 *
 * N threads are downloading list of addresses (which is common for all of the
 * threads and might be modified over the time)
 * Each thread is downloading at most one address at same time
 */

#include <pthread.h>
#include <err.h>
#include <memory>
#include "./ServerAgent.h"  // NOLINT
#include "./DownloaderThread.h"

using crawlcheck::proxy::ServerAgent;
using crawlcheck::proxy::DownloaderThread;

ServerAgent::ServerAgent(int threadsCount):
  threadsRunningMutex(PTHREAD_MUTEX_INITIALIZER), thread_active(0),
  threadsRunningCondition(PTHREAD_COND_INITIALIZER), thread_max(threadsCount) {
  threads = new pthread_t[threadsCount];
  downloaders = new std::unique_ptr<DownloaderThread>[threadsCount];
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

void ServerAgent::run() {
  //TODO(alex): implement
  if (thread_active != 0) {
    err(1, "Already running");
  } else {
    for (int i = 0; i < thread_max; i++) {
      printf("Creating thread #%d\n",i);
      //if (pthread_create(&threads[i], NULL, (NULL), NULL) != 0) {
        //printf("Fail!\n");
      //}
    }
  }
}
