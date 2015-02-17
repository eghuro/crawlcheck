/*
 * AddressList.cc
 * Copyright 2015 Alexandr Mansurov
 *
 * AddressList implementation
 * @see AddressList.h
 *
 */

#include <pthread.h>
#include <deque>
#include <string>
#include "./proxy.h"  // NOLINT
#include "./ServerAgent.h"  // NOLINT
#include "./AddressList.h"  // NOLINT

using crawlcheck::proxy::uri_t;
using crawlcheck::proxy::ServerAgent;
using crawlcheck::proxy::AddressList;

AddressList::AddressList(ServerAgent * sa):
  listMutex(PTHREAD_MUTEX_INITIALIZER), publicMutex(PTHREAD_MUTEX_INITIALIZER),
  availableCondition(PTHREAD_COND_INITIALIZER), list(), serverAgent(sa) {}

AddressList::~AddressList() {
  // wait for all threads to finish
  pthread_mutex_lock(serverAgent->getThreadsRunningMutex());
  while (serverAgent->threadsRunning()) {
    pthread_cond_wait(serverAgent->getThreadsRunningCondition(),
      serverAgent->getThreadsRunningMutex());
  }
  pthread_mutex_unlock(serverAgent->getThreadsRunningMutex());
}

uri_t AddressList::getURI() {
  pthread_mutex_lock(&listMutex);
  if (!list.empty()) {
    uri_t uri = list.front();
    list.pop_front();
    pthread_mutex_unlock(&listMutex);
    return uri;
  } else {
    pthread_mutex_unlock(&listMutex);
    return uri_t();
  }
}

void AddressList::putURI(uri_t address) {
  pthread_mutex_lock(&listMutex);
  list.push_back(address);
  pthread_mutex_unlock(&listMutex);
  pthread_cond_broadcast(&availableCondition);
}

bool AddressList::getURIavailable() {
  bool rv = false;
  pthread_mutex_lock(&listMutex);
  rv = !list.empty();
  pthread_mutex_unlock(&listMutex);
  return rv;
}

pthread_mutex_t* AddressList::getMutex() {
  return &publicMutex;
}

pthread_cond_t* AddressList::getAvailableCondition() {
  return &availableCondition;
}
