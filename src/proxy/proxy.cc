// Copyright 2015 Alexandr Mansurov
#include "./proxy.h"
#include "../db/db.h"
#include "../checker/checker.h"

main(int argc, char **argv) {
  ProxyConfiguration conf;
  conf.setInPoolPort(90);
  conf.setInBacklog(100);

  assert(conf.getInPoolPort() == 90);
  assert(conf.getInBacklog() == 100);

  Database d;
  Checker c;
  Proxy proxy(conf, c, d);

  fprintf(stdout, "Starting proxy\n");
  proxy.start();
}
