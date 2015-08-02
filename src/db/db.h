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

  std::size_t getClientRequestCount();
  ClientRequestIdentifier setClientRequest(const HttpParserResult & request);
  HttpParserResult getClientRequest(const ClientRequestIdentifier & identifier);

  std::size_t getServerResponseCount();
  ServerResponseIdentifier setServerResponse(const HttpParserResult & response);
  HttpParserResult getServerResponse(const ServerResponseIdentifier & identifier);
 private:
  const DatabaseConfiguration & config;
};

#endif  // SRC_DB_DB_H_
