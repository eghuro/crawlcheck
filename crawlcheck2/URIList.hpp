/*
 * URIList.hpp
 *
 *  Created on: 10 Apr 2015
 *      Author: alex
 */

#ifndef URILIST_HPP_
#define URILIST_HPP_

#include <string>
#include <tuple>
#include <map>
#include <deque>

enum RequestState {
	REQUESTED, DOWNLOADED, VERIFIED, ERROR
};

enum RequestType {
	USER, CRAWLER
};

class URIList {

 public:
	static URIList & getInstance();

	void placeRequest(const std::string &, RequestType);
	void changeState(const std::string &, RequestState);
	RequestState getState(const std::string &);

	bool empty();
	std::string pop();
 private:
	typedef std::tuple<std::string, RequestType, RequestState> URIRecord; //uri; user; state
	std::map<std::string, URIRecord> records;
	std::deque<std::string> queue;

	 URIList();
	 URIList(const URIList &);
	 URIList& operator=(const URIList &);
	 ~URIList();

	 static bool allowChange(const RequestState, const RequestState);
	 static URIList * instance;
};




#endif /* URILIST_HPP_ */
