INSERT INTO HTTPmethods (method) VALUES ("GET");
INSERT INTO HTTPmethods (method) VALUES ("POST");
INSERT INTO HTTPmethods (method) VALUES ("PUT");
INSERT INTO HTTPmethods (method) VALUES ("CONNECT");
INSERT INTO HTTPmethods (method) VALUES ("HEAD");
INSERT INTO HTTPmethods (method) VALUES ("DELETE");
INSERT INTO HTTPmethods (method) VALUES ("TRACE");

INSERT INTO verificationStatus(id, status) VALUES (1, "REQUESTED");
INSERT INTO verificationStatus(id, status) VALUES (2, "PROCESSING");
INSERT INTO verificationStatus(id, status) VALUES (3, "VERIFYING");
INSERT INTO verificationStatus(id, status) VALUES (4, "FINISHED - OK");
INSERT INTO verificationStatus(id, status) VALUES (5, "FINISHED - ERRORS");
