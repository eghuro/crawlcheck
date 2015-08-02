// Copyright 2015 Alexandr Mansurov

#ifndef SRC_DB_DB_H_
#define SRC_DB_DB_H_

#include "../proxy/HttpParser.h"

class DatabaseConfiguration {
 public:
  DatabaseConfiguration() {}
};

class Database{
 public:
  typedef std::size_t ClientRequestIdentifier;
  typedef std::size_t ServerResponseIdentifier;

  Database(const DatabaseConfiguration& dbc):config(dbc) {}

  std::size_t getClientRequestCount() {
    return 0;
  }
  ClientRequestIdentifier setClientRequest(const HttpParserResult & request) {
    return 0;
  }
  HttpParserResult getClientRequest(const ClientRequestIdentifier & identifier) {
    return HttpParserResult(HttpParserResultState::REQUEST);
  }

  std::size_t getServerResponseCount() {
    return 0;
  }
  ServerResponseIdentifier setServerResponse(const HttpParserResult & response) {
    return 0;
  }
  HttpParserResult getServerResponse(const ServerResponseIdentifier & identifier) {
    return HttpParserResult(HttpParserResultState::RESPONSE);
  }
 private:
  const DatabaseConfiguration & config;
};

#endif  // SRC_DB_DB_H_
