// Copyright 2015 Alexandr Mansurov
#include "./proxy.h"
#include <memory>
#include "../db/db.h"
#include "../checker/checker.h"
#include "./ProxyConfiguration.h"

int main(int argc, char **argv) {
  std::shared_ptr<ProxyConfiguration> conf = std::make_shared<ProxyConfiguration>();
  conf->setInPoolPort(90);
  conf->setInBacklog(100);

  assert(conf->getInPoolPort() == 90);
  assert(conf->getInBacklog() == 100);

  Database d;
  Checker c;
  Proxy proxy(conf, c, d);

  fprintf(stdout, "Starting proxy\n");
  proxy.start();
}

void Proxy::start() {
  auto r = getAddrInfo();

  auto sockets = bindSockets(r);

  listenSockets(sockets);

  auto pollstr = sockets4poll(sockets);  // needs to be deleted manually!!

  int timeout = -1;  // unlimited
  fprintf(stdout, "Polling ... %d\n", sockets.size());
  for (;;) {
    int poll_ret = poll(pollstr, sockets.size(), timeout);
    if (poll_ret > 0) {
      // success
      const std::size_t mask = POLLIN | POLLPRI;
      for (std::size_t i = 0; i < sockets.size(); i++) {
        bool accepted;
        accepted = ((pollstr[i].revents & mask) == POLLIN);
        accepted = accepted || ((pollstr[i].revents & mask) == POLLPRI);
        if (accepted) {
          handle(pollstr[i].fd, configuration);
        }
      }
    } else if (poll_ret == 0) {
      // timeout
      fprintf(stdout, "Connection timeout\n");
    } else {
      HelperRoutines::error("ERROR polling");
    }
  }

  delete pollstr;

  for (auto it = sockets.begin(); it != sockets.end(); ++it) {
    close(*it);
  }
}

std::vector<int> Proxy::bindSockets(struct addrinfo *r) {
  int socket_fd;
  std::vector<int> sockets;
  struct addrinfo *rorig;

  for (rorig = r; r != NULL; r = r->ai_next) {
    if (r->ai_family != AF_INET && r->ai_family != AF_INET6) continue;
    socket_fd = socket(r->ai_family, r->ai_socktype, r->ai_protocol);
    if (-1 != socket_fd) {
      if (0 == bind(socket_fd, r->ai_addr, r->ai_addrlen)) {
        sockets.push_back(socket_fd);
      } else {
        close(socket_fd);
      }
    } else {
      HelperRoutines::warning("Opening socket failed");
    }
  }

  if (sockets.size() == 0) {
    HelperRoutines::error("ERROR binding");
  }
  freeaddrinfo(rorig);
  return sockets;
}

struct pollfd * Proxy::sockets4poll(const std::vector<int> & sockets) {
  std::size_t size = sockets.size();
  struct pollfd * array = new struct pollfd[size];

  std::size_t index = 0;
  for (auto it = sockets.begin(); it != sockets.end(); ++it, index++) {
    array[index].fd = (*it);
    array[index].events = POLLIN | POLLPRI;
  }

  return array;
}
