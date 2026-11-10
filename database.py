"""SQLite helpers for the ATM-EVM demonstration application."""
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("ATM_EVM_DATABASE", BASE_DIR / "instance" / "atm_evm.db")).expanduser()


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def init_db():
    with connect_database() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS voters (
                voter_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                has_voted INTEGER NOT NULL DEFAULT 0 CHECK (has_voted IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                party TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS election (
                election_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'NOT_STARTED'
                    CHECK (status IN ('NOT_STARTED', 'RUNNING', 'ENDED')),
                start_time TEXT,
                end_time TEXT
            );
            CREATE TABLE IF NOT EXISTS votes (
                vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                election_id INTEGER NOT NULL REFERENCES election(election_id),
                candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id),
                cast_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_votes_election ON votes(election_id);
        """)


@contextmanager
def transaction():
    db = connect_database()
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
