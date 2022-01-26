-- Queries for importing archive of intact previous rephoto projects
-- source flask_rephoto/flaskr/schema.sql
-- source flask_rephoto/flaskr/core_subject.sql
-- UPDATE core_subject SET id=id+1 ORDER BY id DESC;
-- source flask_rephoto/flaskr/core_entry.sql
-- UPDATE core_entry SET subject_id=subject_id+1 ORDER BY subject_id DESC;
-- INSERT INTO post(id, title, imgFile, lat, lng) Select c.id, c.name, c.overlay_url, c.lat, c.lng FROM core_subject c;
-- INSERT IGNORE INTO album(postID, image, timedate, make, model) Select c.subject_id, c.image_url, c.timestamp, c.make, c.model FROM core_entry c, post p WHERE c.subject_id = p.id;
-- DELETE FROM post WHERE (SELECT COUNT(*) FROM album WHERE postID = post.id) = 0 AND post.id != 1;   // This is to clear the empty projects from the system
-- DELETE FROM album WHERE postID IN (SELECT p_id FROM (SELECT id as p_id from post WHERE (SELECT COUNT(*) FROM album WHERE postID = post.id) = 1) as p);   // This is to delete all the one entry posts
-- DELETE FROM post WHERE (SELECT COUNT(*) FROM album WHERE postID = post.id) = 0 AND post.id != 1; // This is to delete all the posts of single entries.

-- MySQL
DROP TABLE IF EXISTS album;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) UNIQUE NOT NULL,
  password TEXT NOT NULL,
  contributions INTEGER DEFAULT 0
);

ALTER TABLE user AUTO_INCREMENT=2;

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  author_id INTEGER NOT NULL DEFAULT 1,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  title TEXT,
  body TEXT,
  imgFile TEXT,
  wd TEXT,
  ht TEXT,
  lat DOUBLE,
  lng DOUBLE,
  tag varchar(8126) DEFAULT 'General',
  archive tinyint(1) DEFAULT 1,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

ALTER TABLE post AUTO_INCREMENT=2;

CREATE TABLE album (
  postID INTEGER NOT NULL,
  image VARCHAR(255) NOT NULL,
  width TEXT NOT NULL,
  height TEXT NOT NULL,
  takerID TEXT NOT NULL,
  timedate DATETIME NOT NULL,
  make VARCHAR(255) DEFAULT '',
  model VARCHAR(255) DEFAULT '',
  tag VARCHAR(8126) DEFAULT 'General',
  name VARCHAR(255) DEFAULT '',
  FOREIGN KEY (postID) REFERENCES post (id),
  PRIMARY KEY (postID, image)
);

INSERT INTO user (id, username, password) VALUES (1, 'admin', 'pbkdf2:sha256:150000$VaXDLBDs$52c82196f76d259e4f3b65170584941f9013863be1d714a532d903cf3ae02329');
INSERT INTO post (id, author_id) VALUES (1, 1);