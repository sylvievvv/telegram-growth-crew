"""SQLite storage for leads (found channels) and drafts (messages waiting for approval)."""
import json
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Iterator

from config import settings

LEAD_STATUSES = ("new", "contacted", "negotiating", "booked", "done", "rejected")

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS leads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    title           TEXT,
    link            TEXT,
    about           TEXT,
    subscribers     INTEGER,
    avg_post_reach  INTEGER,
    err_percent     REAL,
    er_percent      REAL,
    ci_index        REAL,
    language        TEXT,
    admin_contacts  TEXT,      -- JSON list of @usernames / links found in the description
    fraud_score     INTEGER,   -- 0 = looks clean, 100 = almost surely fake
    fraud_reasons   TEXT,      -- JSON list of plain-language reasons
    status          TEXT NOT NULL DEFAULT 'new',
    price           REAL,      -- filled in by hand once the admin answers
    notes           TEXT,
    found_with      TEXT,      -- the search words that found it
    created_at      INTEGER NOT NULL,
    updated_at      INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id     INTEGER REFERENCES leads(id),
    kind        TEXT NOT NULL,          -- 'price_request' | 'swap'
    to_contact  TEXT,
    text        TEXT NOT NULL,
    state       TEXT NOT NULL DEFAULT 'waiting',  -- waiting | approved | rejected
    created_at  INTEGER NOT NULL,
    decided_at  INTEGER
);
"""


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(settings.db_path)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init() -> None:
    with connect() as con:
        con.executescript(SCHEMA)


def _row(r: sqlite3.Row | None) -> dict[str, Any] | None:
    if r is None:
        return None
    d = dict(r)
    for key in ("admin_contacts", "fraud_reasons"):
        if key in d and d[key]:
            d[key] = json.loads(d[key])
    return d


def lead_exists(username: str) -> bool:
    with connect() as con:
        return con.execute("SELECT 1 FROM leads WHERE username = ?", (username.lower(),)).fetchone() is not None


def add_lead(lead: dict[str, Any]) -> int:
    now = int(time.time())
    with connect() as con:
        cur = con.execute(
            """INSERT OR IGNORE INTO leads
               (username, title, link, about, subscribers, avg_post_reach, err_percent, er_percent, ci_index,
                language, admin_contacts, fraud_score, fraud_reasons, status, found_with, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?, 'new', ?, ?, ?)""",
            (
                lead["username"].lower(), lead.get("title"), lead.get("link"), lead.get("about"),
                lead.get("subscribers"), lead.get("avg_post_reach"), lead.get("err_percent"),
                lead.get("er_percent"), lead.get("ci_index"), lead.get("language"),
                json.dumps(lead.get("admin_contacts", [])), lead.get("fraud_score"),
                json.dumps(lead.get("fraud_reasons", [])), lead.get("found_with"), now, now,
            ),
        )
        return cur.lastrowid


def get_lead(lead_id: int) -> dict[str, Any] | None:
    with connect() as con:
        return _row(con.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone())


def list_leads(status: str | None = None, max_fraud: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
    sql, args = "SELECT * FROM leads WHERE 1=1", []
    if status:
        sql += " AND status = ?"
        args.append(status)
    if max_fraud is not None:
        sql += " AND fraud_score <= ?"
        args.append(max_fraud)
    sql += " ORDER BY fraud_score ASC, avg_post_reach DESC LIMIT ?"
    args.append(limit)
    with connect() as con:
        return [_row(r) for r in con.execute(sql, args).fetchall()]


def set_lead_status(lead_id: int, status: str) -> None:
    if status not in LEAD_STATUSES:
        raise ValueError(f"status must be one of {LEAD_STATUSES}")
    with connect() as con:
        con.execute("UPDATE leads SET status = ?, updated_at = ? WHERE id = ?", (status, int(time.time()), lead_id))


def add_draft(lead_id: int, kind: str, to_contact: str | None, text: str) -> int:
    with connect() as con:
        cur = con.execute(
            "INSERT INTO drafts (lead_id, kind, to_contact, text, created_at) VALUES (?,?,?,?,?)",
            (lead_id, kind, to_contact, text, int(time.time())),
        )
        return cur.lastrowid


def get_draft(draft_id: int) -> dict[str, Any] | None:
    with connect() as con:
        return _row(con.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone())


def list_drafts(state: str = "waiting") -> list[dict[str, Any]]:
    with connect() as con:
        return [_row(r) for r in con.execute(
            "SELECT * FROM drafts WHERE state = ? ORDER BY created_at DESC", (state,)).fetchall()]


def update_draft_text(draft_id: int, text: str) -> None:
    with connect() as con:
        con.execute("UPDATE drafts SET text = ? WHERE id = ?", (text, draft_id))


def decide_draft(draft_id: int, state: str) -> None:
    assert state in ("approved", "rejected")
    with connect() as con:
        con.execute("UPDATE drafts SET state = ?, decided_at = ? WHERE id = ?", (state, int(time.time()), draft_id))


def has_open_draft(lead_id: int) -> bool:
    with connect() as con:
        return con.execute(
            "SELECT 1 FROM drafts WHERE lead_id = ? AND state IN ('waiting','approved')", (lead_id,)
        ).fetchone() is not None


def get_setting(key: str) -> str | None:
    with connect() as con:
        r = con.execute("SELECT v FROM settings WHERE k=?", (key,)).fetchone()
    return r["v"] if r else None


def set_setting(key: str, value: str) -> None:
    with connect() as con:
        con.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, value))
