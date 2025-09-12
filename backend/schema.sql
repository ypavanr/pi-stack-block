PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;

CREATE TABLE IF NOT EXISTS blocks (
  id       INTEGER PRIMARY KEY,
  question TEXT NOT NULL,
  answer   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
  id   INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS block_tags (
  block_id INTEGER NOT NULL,
  tag_id   INTEGER NOT NULL,
  PRIMARY KEY (block_id, tag_id),
  FOREIGN KEY (block_id) REFERENCES blocks(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id)   REFERENCES tags(id)   ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_block_tags_block_id ON block_tags (block_id);
CREATE INDEX IF NOT EXISTS idx_block_tags_tag_id   ON block_tags (tag_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_blocks_question_answer_nocase
ON blocks (question COLLATE NOCASE, answer COLLATE NOCASE);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_name_nocase
ON tags (name COLLATE NOCASE);

CREATE VIRTUAL TABLE IF NOT EXISTS blocks_fts
USING fts5(
  question,
  content='blocks',
  content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS blocks_ai
AFTER INSERT ON blocks BEGIN
  INSERT INTO blocks_fts(rowid, question) VALUES (new.id, new.question);
END;

CREATE TRIGGER IF NOT EXISTS blocks_ad
AFTER DELETE ON blocks BEGIN
  INSERT INTO blocks_fts(blocks_fts, rowid, question)
  VALUES ('delete', old.id, old.question);
END;

CREATE TRIGGER IF NOT EXISTS blocks_au
AFTER UPDATE OF question ON blocks BEGIN
  INSERT INTO blocks_fts(blocks_fts, rowid, question)
  VALUES ('delete', old.id, old.question);
  INSERT INTO blocks_fts(rowid, question)
  VALUES (new.id, new.question);
END;

INSERT INTO blocks_fts(rowid, question)
  SELECT b.id, b.question
  FROM blocks b
  WHERE NOT EXISTS (SELECT 1 FROM blocks_fts f WHERE f.rowid = b.id);
