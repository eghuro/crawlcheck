/*
 * AddressListText.cc
 * Copyright 2015 Alexandr Mansurov
 *
 * Simple AddressList test
 */

#include <string>
#include <iostream>
#include "./AddressList.h"

int main(int argc, char ** argv) {
  crawlcheck::proxy::ServerAgent sa(2);
  crawlcheck::proxy::AddressList al(&sa);
  sa.setAddressList(&al);

  crawlcheck::proxy::uri_t u1, u2, u3;
  u1.addr = std::string("google.com");
  u1.port = std::string("80");
  u2.addr = std::string("seznam.cz");
  u2.port = std::string("80");
  u3.addr = std::string("www.mff.cuni.cz");
  u3.port = std::string("80");

  al.putURI(u1);
  al.putURI(u2);
  al.putURI(u3);

  // std::cout << al.getURI().addr<<":"<<al.getURI().port << std::endl;
  // std::cout << al.getURI().addr<<":"<<al.getURI().port << std::endl;
  // std::cout << al.getURI().addr<<":"<<al.getURI().port << std::endl;
  // std::cout << al.getURI().addr<<":"<<al.getURI().port << std::endl;

  sa.run();
}
