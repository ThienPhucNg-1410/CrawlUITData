"""Kho SQLite (phần 5): posts, comments, sessions, warnings. Khóa chính chống trùng."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts(
  post_id TEXT PRIMARY KEY, created_at TEXT, time_raw TEXT, text TEXT,
  reactions INTEGER, n_comments INTEGER, bucket INTEGER, round INTEGER,
  status TEXT DEFAULT 'post_only',   -- post_only | comments_full | comments_partial
  permalink TEXT, collected_at TEXT, session_id TEXT,
  shares INTEGER DEFAULT 0, author TEXT);
CREATE TABLE IF NOT EXISTS comments(
  comment_id TEXT PRIMARY KEY, post_id TEXT, parent_id TEXT, text TEXT,
  created_at TEXT, reactions INTEGER, collected_at TEXT, session_id TEXT,
  author TEXT, time_raw TEXT);
CREATE INDEX IF NOT EXISTS ix_comments_post ON comments(post_id);
CREATE TABLE IF NOT EXISTS sessions(
  session_id TEXT PRIMARY KEY, started_at TEXT, ended_at TEXT,
  stage TEXT, n_new INTEGER DEFAULT 0, n_errors INTEGER DEFAULT 0, note TEXT);
CREATE TABLE IF NOT EXISTS warnings(
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, session_id TEXT, kind TEXT, last_action TEXT);
"""

def connect(path):
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA)
    return conn
