"""Student-data privacy controls.

The design follows the obligations a K-8 classroom tool takes on in California:
FERPA (the district stays in control of education records), COPPA (school-
authorized use for under-13s, educational purpose only), and SOPIPA / AB 1584
(no advertising or profiling, deletion on request, district owns the data).
See docs/PRIVACY.md for the mapping from each requirement to the code below.
"""

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app

from .db import get_db, loads, utcnow

# Unambiguous alphabet so young students can type their access code.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

_PII_PATTERNS = [
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("url", re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.IGNORECASE)),
    ("phone", re.compile(r"(?:\+?1[\s.-]?)?\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")),
    ("address", re.compile(
        r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}"
        r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Way|Blvd|Boulevard)\b\.?"
    )),
    ("id_number", re.compile(r"\b\d{6,}\b")),
    ("name", re.compile(r"\b((?:my name is|my name's|i'm called)\s+)[a-z]+", re.IGNORECASE)),
]


def redact(text: str) -> tuple[str, list[str]]:
    """Strip personal information a child might type before it is stored or
    sent to a model provider. Returns the redacted text and the PII kinds found."""
    found = []
    for kind, pattern in _PII_PATTERNS:
        replacement = r"\1[name]" if kind == "name" else f"[{kind}]"
        text, n = pattern.subn(replacement, text)
        if n:
            found.append(kind)
    return text, found


def new_pseudonym() -> str:
    return "stu_" + secrets.token_hex(6)


def new_access_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))


def new_teacher_token() -> str:
    return secrets.token_urlsafe(32)


def hash_secret(value: str) -> str:
    """Keyed hash so short access codes cannot be brute-forced from a DB dump alone."""
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, value.strip().encode(), hashlib.sha256).hexdigest()


def hash_access_code(code: str) -> str:
    return hash_secret(code.strip().upper())


def audit(actor: str, action: str, student_id: str | None = None, detail: str | None = None) -> None:
    get_db().execute(
        "INSERT INTO audit_log (actor, action, student_id, detail, created_at) VALUES (?, ?, ?, ?, ?)",
        (actor, action, student_id, detail, utcnow()),
    )


def export_student(student_id: str) -> dict:
    """Everything stored about one student, for a parent or district records request."""
    db = get_db()
    s = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    stories = db.execute(
        "SELECT id, topic, learning_goal, target_level, measured_level, text, sources, created_at "
        "FROM stories WHERE student_id = ? ORDER BY id", (student_id,)
    ).fetchall()
    feedback = db.execute(
        "SELECT story_id, author_role, rating, difficulty, flag, comment, created_at "
        "FROM feedback WHERE student_id = ? ORDER BY id", (student_id,)
    ).fetchall()
    return {
        "student": {
            "id": s["id"],
            "grade": s["grade"],
            "target_level": s["target_level"],
            "interests": loads(s["interests"]),
            "avoid_topics": loads(s["avoid_topics"]),
            "consent_status": s["consent_status"],
            "created_at": s["created_at"],
            "last_active_at": s["last_active_at"],
        },
        "stories": [dict(r) | {"sources": loads(r["sources"])} for r in stories],
        "feedback": [dict(r) for r in feedback],
        "exported_at": utcnow(),
    }


def delete_student(student_id: str) -> None:
    """Hard delete. Stories and feedback cascade; the audit trail keeps only the pseudonym."""
    get_db().execute("DELETE FROM students WHERE id = ?", (student_id,))


def purge_expired(retention_days: int) -> dict:
    """Retention enforcement: drop old content and any student whose consent was withdrawn."""
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat(timespec="seconds")
    stories = db.execute("DELETE FROM stories WHERE created_at < ?", (cutoff,)).rowcount
    feedback = db.execute("DELETE FROM feedback WHERE created_at < ?", (cutoff,)).rowcount
    withdrawn = [r["id"] for r in db.execute(
        "SELECT id FROM students WHERE consent_status = 'withdrawn'").fetchall()]
    for sid in withdrawn:
        delete_student(sid)
        audit("system", "purge_withdrawn_student", sid)
    audit("system", "purge_expired", detail=json.dumps(
        {"cutoff": cutoff, "stories": stories, "feedback": feedback, "students": len(withdrawn)}))
    db.commit()
    return {"cutoff": cutoff, "stories": stories, "feedback": feedback, "students": len(withdrawn)}
