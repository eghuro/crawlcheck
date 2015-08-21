// Copyright 2015 alex
#ifndef SRC_PROXY_THREADEDHELPERROUTINES_H_
#define SRC_PROXY_THREADEDHELPERROUTINES_H_

#include "pthread.h"
#include <sstream>
#include "HelperRoutines.h"

class ThreadedHelperRoutines {
public:
  static void lock(pthread_mutex_t * mutex, const std::string & desc) {
    int e = pthread_mutex_lock(mutex);
    if (e != 0) {
      std::ostringstream oss;
      oss << "Lock mutex (" << desc << ") {"<<mutex<<"}";
      HelperRoutines::warning(oss.str(), strerror(e));
    }
  }

  static void unlock(pthread_mutex_t * mutex, const std::string & desc) {
    int e = pthread_mutex_unlock(mutex);
    if (e != 0) {
      std::ostringstream oss;
      oss << "Unlock mutex (" << desc << ") {"<<mutex<<"}";
      HelperRoutines::warning(oss.str(), strerror(e));
    }
  }

  static void broadcast(pthread_cond_t * cond, const std::string & desc) {
    int e = pthread_cond_broadcast(cond);
    if (e != 0) {
      std::ostringstream oss;
      oss << "Broadcast condition (" << desc << ")";
      HelperRoutines::warning(oss.str(), strerror(e));
    }
  }
};

#endif  // SRC_PROXY_THREADEDHELPERROUTINES_H_
