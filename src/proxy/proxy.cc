#include "./proxy.h"
#include "../db/db.h"
#include "../checker/checker.h"

main(int argc, char **argv) {
  ProxyConfiguration conf;
  conf.setInPoolPort(80);
  conf.setInBacklog(100);

  assert (conf.getInPoolPort() == 80);
  assert (conf.getInBacklog() == 100);

  Database d;
  Checker c;
  Proxy proxy(conf, c, d);

  fprintf(stdout, "Starting proxy\n");
  proxy.start();
}
