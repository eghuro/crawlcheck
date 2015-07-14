// Copyright 2015 Alexandr Mansurov

#include "ProxyWorker.h"
#include <stdio.h>
#include <sys/socket.h>
#include <unistd.h>

void* ProxyWorker::threadRoutine(void * arg) {
  int fd = reinterpret_cast<int>(arg);

  int new_fd = accept(fd, NULL, NULL);
  if (new_fd == -1) {
    HelperRoutines::error("accept ERROR");
  }

  int buf_len = 1000;
  char buf[1000];
  fprintf(stderr, ".. connection accepted ..\n");

  int n;
  while ((n = read(new_fd, buf, buf_len)) != 0) {
    if (n == -1) {
      perror("READ");
    } else {
      write(1, buf, n);
    }
  }

  close(new_fd);
  fprintf(stderr, ".. connection closed ..\n");
  return NULL;
}

