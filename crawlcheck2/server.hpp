/*
 * server.hpp
 *
 *  Created on: 11 Apr 2015
 *      Author: alex
 */

#ifndef SERVER_HPP_
#define SERVER_HPP_

class server {
 public:
	void doProcessing();
 private:
	void sendRequest(const std::string & uri);
	void storeResults();
};

#endif /* SERVER_HPP_ */
