"""SQLite access helpers (stdlib sqlite3, one connection per request)."""

import json
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with current_app.open_resource("schema.sql") as f:
        get_db().executescript(f.read().decode("utf-8"))


def loads(value: str | None) -> list:
    return json.loads(value) if value else []


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
