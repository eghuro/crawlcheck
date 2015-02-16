/*
 * ServerAgent.cc
 * Copyright 2015 Alexandr Mansurov
 *
 * N threads are downloading list of addresses (which is common for all of the
 * threads and might be modified over the time)
 * Each thread is downloading at most one address at same time
 */

#include <pthread.h>
#include <stdlib.h>
#include <err.h>
#include <memory>
#include "ServerAgent.h"
#include "DownloaderThread.h"
#include "AddressList.h"

using crawlcheck::proxy::ServerAgent;
using crawlcheck::proxy::DownloaderThread;
using crawlcheck::proxy::AddressList;

ServerAgent::ServerAgent(int threadsCount):
  threadsRunningMutex(PTHREAD_MUTEX_INITIALIZER), thread_active(0),
  threadsRunningCondition(PTHREAD_COND_INITIALIZER), thread_max(threadsCount),
  addrListPtr(nullptr) {
  threads = new pthread_t[threadsCount];
  // downloaders = new std::unique_ptr<DownloaderThread>[threadsCount];
  // downloaders = malloc(threadsCount * sizeof (DownloaderThread));
}

ServerAgent::~ServerAgent() {
  delete [] threads;
  // delete [] downloaders;
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
  if (thread_active != 0) {
    err(1, "Already running");
  } else {
    if(addrListPtr!=nullptr){
      for (int i = 0; i < thread_max; i++) {
        printf("Creating thread #%d\n", i);

        if (pthread_create(&threads[i], NULL, DownloaderThread::work, addrListPtr)
          != 0) {
          printf("Fail!\n");
        } else {
          thread_active++;
        }
      }
    } else {
    	err(2,"AddressList not set in ServerAgent");
    }

    for (int i = 0; i < thread_max; i++) {
      printf("Join %d\n", i);
      pthread_join(threads[i], NULL);
      thread_active--;
    }
  }
}

void ServerAgent::setAddressList(AddressList * al) {
  addrListPtr = al;
}
