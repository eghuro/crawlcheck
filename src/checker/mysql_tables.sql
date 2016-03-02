CREATE TABLE verificationStatus (
  id INTEGER PRIMARY KEY,
  status VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE HTTPmethods (
  method VARCHAR(10) PRIMARY KEY
);

INSERT INTO HTTPmethods (method) VALUES ("GET");
INSERT INTO HTTPmethods (method) VALUES ("POST");
INSERT INTO HTTPmethods (method) VALUES ("PUT");
INSERT INTO HTTPmethods (method) VALUES ("CONNECT");
INSERT INTO HTTPmethods (method) VALUES ("HEAD");
INSERT INTO HTTPmethods (method) VALUES ("DELETE");
INSERT INTO HTTPmethods (method) VALUES ("TRACE");

CREATE TABLE transactions (
  id INTEGER PRIMARY KEY,
  method VARCHAR(10) NOT NULL,
  uri VARCHAR(255) NOT NULL,
  responseStatus INTEGER,
  contentType VARCHAR(255),
  content TEXT,
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

CREATE TABLE finding (
  id INTEGER PRIMARY KEY NOT NULL,
  responseId INT UNSIGNED NOT NULL,
  FOREIGN KEY(responseId)
    REFERENCES transactions(id)
    ON DELETE CASCADE
);

CREATE TABLE link (
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

CREATE TABLE defectType (
  id INTEGER PRIMARY KEY NOT NULL,
  type VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS defect (
  findingId INTEGER PRIMARY KEY NOT NULL,
  type INT UNSIGNED NOT NULL,
  location INT UNSIGNED NOT NULL,
  evidence TEXT NOT NULL,
  FOREIGN KEY (findingId)
    REFERENCES finding(id)
    ON DELETE CASCADE,
  FOREIGN KEY (type)
    REFERENCES defectType(id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS annotation (
  id INTEGER PRIMARY KEY NOT NULL,
  findingId INT UNSIGNED NOT NULL,
  comment TEXT NOT NULL,
  author VARCHAR(255) NOT NULL,
  created DATETIME NOT NULL,
  FOREIGN KEY (findingId)
    REFERENCES finding(id)
    ON DELETE CASCADE
);

INSERT INTO verificationStatus(id, status) VALUES (1, "REQUESTED");
INSERT INTO verificationStatus(id, status) VALUES (2, "RETRIEVING");
INSERT INTO verificationStatus(id, status) VALUES (3, "RESPONDED");
INSERT INTO verificationStatus(id, status) VALUES (4, "PROCESSING");
INSERT INTO verificationStatus(id, status) VALUES (5, "FINISHED");

INSERT INTO defectType(type, description) VALUES ("badlink", "Invalid link");
INSERT INTO defectType(type, description) VALUES ("stylesheet", "Stylesheet error");
INSERT INTO defectType(type, description) VALUES ("badtype", "Content-type empty");
INSERT INTO defectType(type, description) VALUES ("seo:huge_internal", "Big internal CSS");
INSERT INTO defectType(type, description) VALUES ("seo:duplicit_inline", "Duplicit inline CSS");
