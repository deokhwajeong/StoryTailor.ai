"""Authentication: teachers use a bearer token; students use a short access code
their teacher hands out on paper. Neither carries a real name."""

from functools import wraps

from flask import abort, g, request

from .db import get_db, utcnow
from .privacy import hash_access_code, hash_secret


def teacher_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            abort(401, "Teacher token required.")
        row = get_db().execute(
            "SELECT * FROM teachers WHERE token_hash = ?", (hash_secret(header[7:]),)
        ).fetchone()
        if row is None:
            abort(401, "Invalid teacher token.")
        g.teacher = row
        g.actor = f"teacher:{row['id']}"
        return view(*args, **kwargs)
    return wrapper


def student_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        code = request.headers.get("X-Student-Code", "")
        if not code:
            abort(401, "Student access code required.")
        db = get_db()
        row = db.execute(
            "SELECT * FROM students WHERE access_code_hash = ?", (hash_access_code(code),)
        ).fetchone()
        if row is None:
            abort(401, "Invalid access code.")
        if row["consent_status"] != "school_authorized":
            abort(403, "This account is paused. Please ask your teacher.")
        db.execute("UPDATE students SET last_active_at = ? WHERE id = ?", (utcnow(), row["id"]))
        g.student = row
        g.actor = f"student:{row['id']}"
        return view(*args, **kwargs)
    return wrapper


def teacher_owns_student(student_id: str):
    row = get_db().execute(
        "SELECT s.* FROM students s JOIN classrooms c ON c.id = s.classroom_id "
        "WHERE s.id = ? AND c.teacher_id = ?", (student_id, g.teacher["id"])
    ).fetchone()
    if row is None:
        abort(404, "Student not found in your classrooms.")
    return row


def teacher_owns_classroom(classroom_id: int):
    row = get_db().execute(
        "SELECT * FROM classrooms WHERE id = ? AND teacher_id = ?", (classroom_id, g.teacher["id"])
    ).fetchone()
    if row is None:
        abort(404, "Classroom not found.")
    return row
