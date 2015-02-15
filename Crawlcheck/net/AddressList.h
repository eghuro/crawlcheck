/*
 * AddressList.h
 * Copyright 2015 Alexandr Mansurov
 *
 * list of addresses to be downloaded by server agent (common for all threads,
 * may be modified throughout the time)
 */

#ifndef _NET_ADDRESSLIST_H_  // NOLINT
#define _NET_ADDRESSLIST_H_  // NOLINT

#include <pthread.h>
#include <string>
#include <deque>
#include "./ServerAgent.h"  // NOLINT

namespace crawlcheck {
namespace proxy {
typedef std::string uri_t;

class ServerAgent;
class AddressList {
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

 private:
  pthread_mutex_t listMutex;
  std::deque<uri_t> list;
  crawlcheck::proxy::ServerAgent* serverAgent;
};
}  // namespace proxy
}  // namespace crawlcheck


#endif /* _NET_ADDRESSLIST_H_ */  // NOLINT
