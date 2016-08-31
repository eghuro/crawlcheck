CREATE TABLE IF NOT EXISTS verificationStatus (
  id INTEGER PRIMARY KEY,
  status VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS HTTPmethods (
  method VARCHAR(10) PRIMARY KEY
);

INSERT INTO HTTPmethods (method) VALUES ("GET");
INSERT INTO HTTPmethods (method) VALUES ("POST");
INSERT INTO HTTPmethods (method) VALUES ("PUT");
INSERT INTO HTTPmethods (method) VALUES ("CONNECT");
INSERT INTO HTTPmethods (method) VALUES ("HEAD");
INSERT INTO HTTPmethods (method) VALUES ("DELETE");
INSERT INTO HTTPmethods (method) VALUES ("TRACE");

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY,
  method VARCHAR(10) NOT NULL,
  uri VARCHAR(255) NOT NULL,
  responseStatus INTEGER,
  contentType VARCHAR(255),
  content VARCHAR(255),
  verificationStatusId INTEGER,
  origin VARCHAR(255),
  depth INTEGER NOT NULL,
  FOREIGN KEY (verificationStatusId) 
    REFERENCES verificationStatus(id)
    ON DELETE CASCADE,
  FOREIGN KEY (method)
    REFERENCES HTTPmethods(method)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS finding (
  id INTEGER PRIMARY KEY NOT NULL,
  responseId INT UNSIGNED NOT NULL,
  FOREIGN KEY(responseId)
    REFERENCES transactions(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS link (
  findingId INTEGER PRIMARY KEY NOT NULL,
  toUri VARCHAR(255) NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT false,
  requestId INT UNSIGNED,
  FOREIGN KEY (findingId)
    REFERENCES finding(id)
    ON DELETE CASCADE,
  FOREIGN KEY (requestId)
    REFERENCES transactions(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS defectType (
  id INTEGER PRIMARY KEY NOT NULL,
  type VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS defect (
  findingId INTEGER PRIMARY KEY NOT NULL,
  type INT UNSIGNED NOT NULL,
  evidence TEXT NOT NULL,
  severity REAL NOT NULL DEFAULT 0.5, 
  FOREIGN KEY (findingId)
    REFERENCES finding(id)
    ON DELETE CASCADE,
  FOREIGN KEY (type)
    REFERENCES defectType(id)
    ON DELETE CASCADE
);

INSERT INTO verificationStatus(id, status) VALUES (1, "REQUESTED");
INSERT INTO verificationStatus(id, status) VALUES (2, "PROCESSING");
INSERT INTO verificationStatus(id, status) VALUES (3, "VERIFYING");
INSERT INTO verificationStatus(id, status) VALUES (4, "FINISHED - OK");
INSERT INTO verificationStatus(id, status) VALUES (5, "FINISHED - ERRORS");
