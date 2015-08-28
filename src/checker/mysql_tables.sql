USE crawlcheck;

CREATE TABLE IF NOT EXISTS verificationStatus (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  status VARCHAR(255) NOT NULL,
  description TEXT,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS transaction (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT, 
  method ENUM( 'GET', 'POST', 'PUT', 'CONNECT', 'HEAD', 'DELETE', 'TRACE') NOT NULL,
  uri VARCHAR(255) NOT NULL,
  responseStatus INT UNSIGNED,
  contentType VARCHAR(255),
  content TEXT CHARACTER SET utf8 COLLATE utf8_general_ci,
  verificationStatusId INT UNSIGNED,
  origin ENUM( 'CLIENT', 'CHECKER'),
  rawRequest BLOB,
  rawResponse BLOB,
  PRIMARY KEY(id),
  FOREIGN KEY (verificationStatusId) 
    REFERENCES verificationStatus(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS finding (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  responseId INT UNSIGNED NOT NULL,
  PRIMARY KEY(id),
  FOREIGN KEY(responseId)
    REFERENCES transaction(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS link (
  findingId INT UNSIGNED NOT NULL,
  toUri VARCHAR(255) NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT false,
  requestId INT UNSIGNED,
  PRIMARY KEY(findingId),
  FOREIGN KEY (findingId)
    REFERENCES finding(id)
    ON DELETE CASCADE,
  FOREIGN KEY (requestId)
    REFERENCES transaction(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS defectType (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  type VARCHAR(255) NOT NULL,
  description TEXT,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS defect (
  findingId INT UNSIGNED NOT NULL,
  type INT UNSIGNED NOT NULL,
  location INT UNSIGNED NOT NULL,
  evidence TEXT NOT NULL,
  PRIMARY KEY(findingId),
  FOREIGN KEY (findingId)
    REFERENCES finding(id)
    ON DELETE CASCADE,
  FOREIGN KEY (type)
    REFERENCES defectType(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS annotation (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  findingId INT UNSIGNED NOT NULL,
  comment TEXT NOT NULL,
  author VARCHAR(255) NOT NULL,
  created DATETIME NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (findingId)
    REFERENCES finding(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT INTO verificationStatus(id, status) VALUES (1, "REQUESTED");
INSERT INTO verificationStatus(id, status) VALUES (2, "RETRIEVING");
INSERT INTO verificationStatus(id, status) VALUES (3, "RESPONDED");
INSERT INTO verificationStatus(id, status) VALUES (4, "PROCESSING");
INSERT INTO verificationStatus(id, status) VALUES (5, "FINISHED");
