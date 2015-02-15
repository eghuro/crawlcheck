/*
 * DownloaderThread.h
 *
 *  Created on: 15 Feb 2015
 *      Author: alex
 */

#ifndef _NET_DOWNLOADERTHREAD_H_
#define _NET_DOWNLOADERTHREAD_H_

namespace crawlcheck {
namespace proxy {
class DownloaderThread {
 public:
  static void * work(void *);
};

} /* namespace proxy */
} /* namespace crawlcheck */
#endif /* _NET_DOWNLOADERTHREAD_H_ */
