import os, pathlib, sqlite3, time
from contextlib import contextmanager

_DEFAULT = str(pathlib.Path(__file__).parent.parent / "data" / "students.db")

def path():
    return os.getenv("DB_PATH", _DEFAULT)

SCHEMA = """
CREATE TABLE students(id TEXT PRIMARY KEY, name TEXT, programme TEXT, batch TEXT, email TEXT);
CREATE TABLE fees(student_id TEXT PRIMARY KEY, total INT, paid INT, due_date TEXT, status TEXT);
CREATE TABLE scholarships(student_id TEXT, name TEXT, status TEXT, amount INT);
CREATE TABLE tickets(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT, subject TEXT, body TEXT, ts REAL);
CREATE TABLE memory(student_id TEXT, key TEXT, value TEXT, ts REAL, PRIMARY KEY(student_id, key));
"""

TABLES = ("students", "fees", "scholarships", "tickets", "memory")

def is_app_db():
    return os.path.abspath(path()) == os.path.abspath(_DEFAULT)

@contextmanager
def connect():
    """Always-closed connection. NOTE: `with sqlite3.connect()` alone only commits/rolls back and leaves the
    connection (and file handle) open, which breaks file deletion on Windows. Use this instead."""
    p = path()
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    except BaseException:
        c.rollback()
        raise
    finally:
        c.close()

def _init():
    """(Re)create schema + synthetic seed inside ONE closed connection. Never deletes the file."""
    with connect() as c:
        for t in TABLES:                      # fixed constant names, not user input
            c.execute(f"DROP TABLE IF EXISTS {t}")
        c.executescript(SCHEMA)
        c.executemany("INSERT INTO students VALUES(?,?,?,?,?)", [
            ("S101", "Aarav Mehta", "PGDM Big Data Analytics", "2025-27", "aarav@example.edu"),
            ("S102", "Diya Rao", "PGDM AI & Data Science", "2025-27", "diya@example.edu"),
            ("S103", "Kabir Singh", "PGDM Big Data Analytics", "2025-27", "kabir@example.edu")])
        c.executemany("INSERT INTO fees VALUES(?,?,?,?,?)", [
            ("S101", 120000, 75000, "2026-11-05", "Partially paid"),
            ("S102", 120000, 120000, "2026-11-05", "Paid"),
            ("S103", 120000, 0, "2026-10-30", "Pending")])
        c.executemany("INSERT INTO scholarships VALUES(?,?,?,?)", [
            ("S102", "Merit Scholarship", "Approved", 30000),
            ("S103", "Need-based Scholarship", "Under review", 20000)])

def reset(allow_app_db=False):
    """Reset CONTENTS of the current DB (drop/recreate tables, reseed). Does not delete the file.
    Refuses to touch the application database (data/students.db) unless explicitly allowed."""
    if is_app_db() and not allow_app_db:
        raise RuntimeError("refusing to reset the application database; set DB_PATH to an isolated file")
    _init()

def ensure():
    """Create the DB on first run only. Never wipes existing data."""
    exists = os.path.exists(path())
    if exists:
        with connect() as c:
            have = {r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if set(TABLES) <= have:
            return
        if have & set(TABLES):
            raise RuntimeError("database has an unexpected schema; not modifying it")
    _init()
