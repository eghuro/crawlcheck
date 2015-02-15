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
  crawlcheck::proxy::ServerAgent sa(4);
  crawlcheck::proxy::AddressList al(&sa);
  sa.setAddressList(&al);

  al.putURI(std::string("google.com"));
  al.putURI(std::string("seznam.cz"));
  al.putURI(std::string("www.mff.cuni.cz"));

  std::cout << al.getURI() << std::endl;
  std::cout << al.getURI() << std::endl;
  std::cout << al.getURI() << std::endl;
  std::cout << al.getURI() << std::endl;

  sa.run();
}
