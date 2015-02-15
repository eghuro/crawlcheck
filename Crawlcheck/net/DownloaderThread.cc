/*
 * DownloaderThread.cpp
 * Copyright 2015 Alexandr Mansurov
 *
 * Actual downloading done here
 */

#include <unistd.h>
#include "DownloaderThread.h"
#include "AddressList.h"

using crawlcheck::proxy::DownloaderThread;

void * DownloaderThread::work(void *) {
  // TODO(alex): downloading
  printf("Hello\n");
  sleep(3);
  printf("Goodbye\n");
  return nullptr;
}
