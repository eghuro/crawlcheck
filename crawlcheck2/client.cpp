/*
 * client.cpp
 *
 *  Created on: 10 Apr 2015
 *      Author: alex
 */

#include "client.hpp"
#include "URIList.hpp"
#include <string>
#include <memory>

std::string * client::requestURI(const std::string & uri) {
	URIList::getInstance().placeUserRequest(uri);
}

