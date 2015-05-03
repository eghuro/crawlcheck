/*
 * message.h
 * Copyright 2015 Alexandr Mansurov
 */

#ifndef CRAWLCHECK_NET_MESSAGE_H_
#define CRAWLCHECK_NET_MESSAGE_H_

namespace crawlcheck {
namespace proxy {
class HTTPStatus {};

class HTTPStatusInformative : HTTPStatus {
	static const unsigned int CONTINUE = 100;
	static const unsigned int SWITCHING_PROTOCOLS = 101;
};

class HTTPStatusSuccess : HTTPStatus {
	static const unsigned int OK = 200;
	static const unsigned int CREATED = 201;
	static const unsigned int ACCEPTED = 202;
	static const unsigned int NON_AUTHORITATIVE_INFORMATION = 203;
	static const unsigned int NO_CONTENT = 204;
	static const unsigned int RESET_CONTENT = 205;
	static const unsigned int PARTIAL_CONTENT = 206;
};

class HTTPRedirection : HTTPStatus {
	static const unsigned int MULTIPLE_CHOICES = 300;
	static const unsigned int MOVED_PERMANENTLY = 301;
	static const unsigned int MOVED_TEMPORARILY = 302;
	static const unsigned int SEE_OTHER = 303;
	static const unsigned int NOT_MODIFIED = 304;
	static const unsigned int USE_PROXY = 305;
};

class HTTPClientError : HTTPStatus {
	static const unsigned int BAD_REQUEST = 400;
	static const unsigned int UNAUTHORIZED = 401;
	static const unsigned int PAYMENT_REQUIRED = 402;
	static const unsigned int FORBIDDEN = 403;
	static const unsigned int NOT_FOUND = 404;
	static const unsigned int METHOD_NOT_ALLOWED = 405;
	static const unsigned int NOT_ACCEPTABLE = 406;
	static const unsigned int PROXY_AUTHENTICATION_REQUIRED = 407;
	static const unsigned int REQUEST_TIMEOUT = 408;
	static const unsigned int CONFLICT = 409;
	static const unsigned int GONE = 410;
	static const unsigned int LENGTH_REQUIRED = 411;
	static const unsigned int PRECONDITION_FAILED = 412;
	static const unsigned int REQUEST_ENTITY_TOO_LARGE = 413;
	static const unsigned int REQUEST_URI_TOO_LARGE = 414;
};

class HTTPServerError : HTTPStatus {
	static const unsigned int INTERNAL_SERVER_ERROR = 500;
	static const unsigned int NOT_IMPLEMENTED = 501;
	static const unsigned int BAD_GATEWAY = 502;
	static const unsigned int SERVICE_UNAVAILABLE = 503;
	static const unsigned int GATEWAY_TIMEOUT = 504;
	static const unsigned int HTTP_VERSION_NOT_SUPPORTED = 505;
};

class HTTPResponse {
};
}  // namespace proxy
}  // namespace crawlcheck

#endif  // CRAWLCHECK_NET_MESSAGE_H_
