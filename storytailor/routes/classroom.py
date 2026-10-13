"""Teacher endpoints: classrooms, pseudonymous student accounts, feedback summary."""

import json

from flask import Blueprint, abort, g, jsonify, request

from ..auth import teacher_owns_classroom, teacher_required
from ..db import get_db, loads, utcnow
from ..personalization import default_level
from ..privacy import audit, hash_access_code, new_access_code, new_pseudonym

bp = Blueprint("classroom", __name__, url_prefix="/api/classrooms")

MAX_BATCH = 40


@bp.post("")
@teacher_required
def create_classroom():
    data = request.get_json(force=True)
    name, grade = data.get("name", "").strip(), data.get("grade")
    if not name or not isinstance(grade, int) or not 0 <= grade <= 8:
        abort(400, "name and grade (0-8, 0 = kindergarten) are required.")
    db = get_db()
    cur = db.execute(
        "INSERT INTO classrooms (teacher_id, name, grade, created_at) VALUES (?, ?, ?, ?)",
        (g.teacher["id"], name, grade, utcnow()),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "name": name, "grade": grade}), 201


@bp.post("/<int:classroom_id>/students")
@teacher_required
def add_students(classroom_id):
    """Create N pseudonymous accounts. Access codes are returned once and only
    their keyed hash is stored; the teacher prints them for the roster."""
    room = teacher_owns_classroom(classroom_id)
    data = request.get_json(force=True)
    count = data.get("count", 1)
    if not isinstance(count, int) or not 1 <= count <= MAX_BATCH:
        abort(400, f"count must be 1-{MAX_BATCH}.")
    interests = [str(i)[:40] for i in data.get("interests", [])][:5]
    db = get_db()
    created = []
    for _ in range(count):
        sid, code = new_pseudonym(), new_access_code()
        db.execute(
            "INSERT INTO students (id, classroom_id, access_code_hash, grade, target_level, interests, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sid, classroom_id, hash_access_code(code), room["grade"], default_level(room["grade"]),
             json.dumps(interests), utcnow()),
        )
        audit(g.actor, "create_student", sid)
        created.append({"student_id": sid, "access_code": code})
    db.commit()
    return jsonify({"students": created, "note": "Access codes are shown only once."}), 201


@bp.get("/<int:classroom_id>/students")
@teacher_required
def list_students(classroom_id):
    teacher_owns_classroom(classroom_id)
    rows = get_db().execute(
        "SELECT s.id, s.grade, s.target_level, s.interests, s.consent_status, s.last_active_at, "
        "COUNT(st.id) AS stories FROM students s LEFT JOIN stories st ON st.student_id = s.id "
        "WHERE s.classroom_id = ? GROUP BY s.id ORDER BY s.created_at", (classroom_id,)
    ).fetchall()
    return jsonify([dict(r) | {"interests": loads(r["interests"])} for r in rows])


@bp.get("/<int:classroom_id>/feedback-summary")
@teacher_required
def feedback_summary(classroom_id):
    """What the class is telling us: difficulty fit, ratings, and flagged stories."""
    teacher_owns_classroom(classroom_id)
    db = get_db()
    base = "FROM feedback f JOIN students s ON s.id = f.student_id WHERE s.classroom_id = ?"
    difficulty = {r["difficulty"]: r["n"] for r in db.execute(
        f"SELECT f.difficulty, COUNT(*) AS n {base} AND f.difficulty IS NOT NULL GROUP BY f.difficulty",
        (classroom_id,))}
    rating = db.execute(f"SELECT AVG(f.rating) AS avg, COUNT(f.rating) AS n {base}", (classroom_id,)).fetchone()
    flags = db.execute(
        f"SELECT f.story_id, f.flag, f.author_role, f.comment, f.created_at {base} AND f.flag IS NOT NULL "
        "ORDER BY f.id DESC LIMIT 50", (classroom_id,)
    ).fetchall()
    levels = db.execute(
        "SELECT AVG(target_level) AS avg_target, MIN(target_level) AS min_target, "
        "MAX(target_level) AS max_target FROM students WHERE classroom_id = ?", (classroom_id,)
    ).fetchone()
    return jsonify({
        "difficulty": {k: difficulty.get(k, 0) for k in ("too_easy", "just_right", "too_hard")},
        "rating": {"average": round(rating["avg"], 2) if rating["avg"] else None, "count": rating["n"]},
        "flags": [dict(r) for r in flags],
        "levels": dict(levels),
    })
