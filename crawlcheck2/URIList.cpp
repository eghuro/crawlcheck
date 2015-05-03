/*
 * URIList.cpp
 *
 *  Created on: 10 Apr 2015
 *      Author: alex
 */

#include "URIList.hpp"
#include <tuple>
#include <map>
URIList * URIList::instance = nullptr;

static URIList& URIList::getInstance() {
	if (instance == nullptr) {
		return new URIList();
	}
	return *instance;
}

void URIList::placeRequest(const std::string & uri, RequestType type) {
	records.insert(uri, std::make_tuple(uri, type, RequestState::REQUESTED));
	queue.push_back(uri);
}

void URIList::changeState(const std::string & uri, RequestState newState) {
	auto record = records.find(uri);
	if (record != records.end()) {
		if (allowChange(std::get< 2 >((*record) -> second), newState)) {
		  std::get<2>((*record)->second) = newState;
		}
	}
}

bool URIList::allowChange(const RequestState from, const RequestState to) {
	switch (from) {
	  case REQUESTED: return (to == RequestState::DOWNLOADED) || (to == RequestState::ERROR); break;
	  case DOWNLOADED: return (to == RequestState::VERIFIED) || (to == RequestState::ERROR); break;
	  case VERIFIED: return (to == RequestState::ERROR); break;
	  case ERROR: return false;
	  default: return false;
	  //TODO vlastnost state
	}
}

RequestState URIList::getState(const std::string& uri) {
	auto record = records.find(uri);
	if (record != records.end()) {
		return std::get<2>((*record)->second);
	} else {
		return RequestState::ERROR;
	}
}

bool URIList::empty() {
	return queue.empty();
}

std::string URIList::pop() {
	auto ret = queue.front();
	queue.pop_front();
	return ret;
}
