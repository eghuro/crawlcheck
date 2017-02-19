CREATE TABLE IF NOT EXISTS verificationStatus (
  id INTEGER PRIMARY KEY,
  status VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS HTTPmethods (
  method VARCHAR(10) PRIMARY KEY
);

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

CREATE TABLE IF NOT EXISTS defectType (
  id INTEGER PRIMARY KEY NOT NULL,
  type VARCHAR(255) NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS finding (
  id INTEGER PRIMARY KEY NOT NULL,
  responseId INT UNSIGNED NOT NULL,
  findingType VARCHAR(1) NOT NULL,

  link_toUri INTEGER NULL,
  link_processed BOOLEAN NULL DEFAULT false,
  link_requestId INT UNSIGNED,

  defect_type INT UNSIGNED NULL,
  defect_evidence TEXT NULL,
  defect_severity REAL NULL DEFAULT 0.5,

  cookie_name VARCHAR(255) NULL,
  cookie_value VARCHAR(255) NULL,

  FOREIGN KEY(responseId)
    REFERENCES transactions(id)
    ON DELETE CASCADE,

  FOREIGN KEY (link_requestId)
    REFERENCES transactions(id)
    ON DELETE CASCADE,
  FOREIGN KEY (defect_type)
    REFERENCES decectType(id)
    ON DELETE CASCADE
);
