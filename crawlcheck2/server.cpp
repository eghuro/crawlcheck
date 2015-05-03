/*
 * server.cpp
 *
 *  Created on: 11 Apr 2015
 *      Author: alex
 */

#include "server.hpp"
#include "Poco/Net/HTTPClientSession.h"
#include "Poco/Net/HTTPRequest.h"

void server::doProcessing() {
	URIList list = URIList::getInstance();

	while (!list.empty()) {
		auto uri = list.pop();
		sendRequest(uri);
	}
}

void server::sendRequest(const std::string & verifyUri) {
	const std::string validatorUri = "http://validator.w3.org/check";
	HTTPRequest request(HTTPRequest::HTTP_POST,validatorUri);
	request.add("uri", verifyUri);
	request.add("output", "soap12");

	HTTPClientSession session(validatorUri);
	session.sendRequest(request);

	HTTPResponse response;
	auto stream = session.receiveResponse(response);
	if (response.getStatus() == HTTP_OK) {
		// parse header?
		// parse SOAP
	}
}
