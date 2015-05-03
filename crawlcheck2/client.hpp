/*
 * client.hpp
 *
 *  Created on: 10 Apr 2015
 *      Author: alex
 */

#ifndef CLIENT_HPP_
#define CLIENT_HPP_
#include <string>

class client {
 public:
	std::string * requestURI(const std::string & uri);
};


#endif /* CLIENT_HPP_ */
