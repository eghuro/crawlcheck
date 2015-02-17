/*
 * AddressList.h
 * Copyright 2015 Alexandr Mansurov
 *
 * list of addresses to be downloaded by server agent (common for all threads,
 * may be modified throughout the time)
 */

#ifndef CRAWLCHECK_NET_ADDRESSLIST_H_
#define CRAWLCHECK_NET_ADDRESSLIST_H_

#include <pthread.h>
#include <string>
#include <deque>
#include "./proxy.h"  // NOLINT
#include "./ServerAgent.h"  // NOLINT

namespace crawlcheck {
namespace proxy {
class AddressList {
// BEWARE: need to differentiate user generated and crawler generated traffic
// for performance
 public:
  explicit AddressList(crawlcheck::proxy::ServerAgent *sa);
  AddressList();
  ~AddressList();

  // zatim zakazano:
  AddressList(const AddressList& other) = delete;  // copy constructor
  AddressList& operator= (const AddressList& other) = delete;  // copy assment
  AddressList& operator= (AddressList&& other) = delete;  // move assment optor


  /**
   * Called by a downloader thread
   * Return an URI to be downloaded
   *
   * @return address to be downloaded or null
   */
  uri_t getURI();

  /**
   * Insert an URI to be downloaded
   * @param address address to be downloaded
   */
  void putURI(uri_t address);

  /**
   * Any addresses available in list?
   */
  bool getURIavailable();

  pthread_mutex_t* getMutex();
  pthread_cond_t* getAvailableCondition();

 private:
  pthread_mutex_t listMutex, publicMutex;
  pthread_cond_t availableCondition;
  std::deque<uri_t> list;
  crawlcheck::proxy::ServerAgent* serverAgent;
};
}  // namespace proxy
}  // namespace crawlcheck


#endif  // CRAWLCHECK_NET_ADDRESSLIST_H_
