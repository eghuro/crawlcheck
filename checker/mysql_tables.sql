CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY NOT NULL,
  method VARCHAR(10) NOT NULL,
  uri VARCHAR(255) NOT NULL,
  responseStatus INTEGER,
  contentType VARCHAR(255),
  verificationStatus VARCHAR(20),
  depth INTEGER NOT NULL,
  expected VARCHAR(255),
  data TEXT
);

CREATE INDEX IF NOT EXISTS transactions_uri ON transactions (uri);

CREATE TABLE IF NOT EXISTS aliases (
  transactionId INTEGER NOT NULL,
  uri VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS param (
  findingId INTEGER PRIMARY KEY NOT NULL,
  responseId INTEGER NOT NULL,
  key VARCHAR(255) NOT NULL,
  value VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS link (
  findingId INTEGER PRIMARY KEY NOT NULL,
  toUri VARCHAR(255) NOT NULL,
  responseId INT UNSIGNED NOT NULL,
  requestId INT UNSIGNED,
  processed BOOLEAN,
  allowed BOOLEAN,
  good BOOLEAN
);

CREATE INDEX IF NOT EXISTS link_request_id ON link (requestId);
CREATE INDEX IF NOT EXISTS link_processed ON link (processed);
CREATE INDEX IF NOT EXISTS link_response_id ON link (responseId);
CREATE INDEX IF NOT EXISTS link_to_uri ON link (toUri);

CREATE TABLE IF NOT EXISTS defectType (
  id INTEGER PRIMARY KEY NOT NULL,
  type VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS defect (
  findingId INTEGER PRIMARY KEY NOT NULL,
  type VARCHAR(255) NOT NULL,
  evidence TEXT NOT NULL,
  severity REAL NOT NULL DEFAULT 0.5,
  responseId INT UNSIGNED NOT NULL
);

CREATE TABLE IF NOT EXISTS cookies (
  findingId INTEGER PRIMARY KEY NOT NULL,
  name VARCHAR(255) NOT NULL,
  value VARCHAR(255) NOT NULL,
  secure BOOLEAN,
  httpOnly BOOLEAN,
  path VARCHAR(255),
  responseId INT UNSIGNED NOT NULL
);

CREATE TABLE IF NOT EXISTS headers (
  findingId INTEGER PRIMARY KEY NOT NULL,
  name VARCHAR(255) NOT NULL,
  value VARCHAR(255) NOT NULL,
  responseId INT UNSIGNED NOT NULL
);
