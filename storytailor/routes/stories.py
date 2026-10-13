"""Student story generation and feedback (students and teachers)."""

import json

from flask import Blueprint, abort, current_app, g, jsonify, request

from ..auth import student_required, teacher_owns_student, teacher_required
from ..db import get_db, loads, utcnow
from ..llm import get_provider
from ..personalization import Profile, UnsafeRequest, adjust_level, generate_story
from ..privacy import audit, redact

bp = Blueprint("stories", __name__, url_prefix="/api/stories")

DIFFICULTY = {"too_easy", "just_right", "too_hard"}
FLAGS = {"inappropriate", "inaccurate", "off_topic"}
RECENT_VOTES = 5


def _profile(row) -> Profile:
    return Profile(row["grade"], row["target_level"], loads(row["interests"]), loads(row["avoid_topics"]))


@bp.post("")
@student_required
def create_story():
    data = request.get_json(force=True)
    topic, topic_pii = redact(str(data.get("topic", "")).strip()[:120])
    goal, goal_pii = redact(str(data.get("learning_goal") or "").strip()[:120])
    if not topic:
        abort(400, "topic is required.")
    try:
        result = generate_story(
            get_provider(), _profile(g.student), topic, goal or None,
            current_app.config["LEVEL_TOLERANCE"],
        )
    except UnsafeRequest as e:
        abort(422, str(e))
    db = get_db()
    cur = db.execute(
        "INSERT INTO stories (student_id, topic, learning_goal, target_level, measured_level, text, sources, "
        "attempts, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (g.student["id"], topic, goal or None, result["target_level"], result["measured_level"],
         result["text"], json.dumps(result["sources"]), result["attempts"], utcnow()),
    )
    if topic_pii or goal_pii:
        audit(g.actor, "redacted_input", g.student["id"], ",".join(sorted(set(topic_pii + goal_pii))))
    db.commit()
    return jsonify({"id": cur.lastrowid, "topic": topic, **result,
                    "redacted": sorted(set(topic_pii + goal_pii))}), 201


@bp.get("")
@student_required
def my_stories():
    rows = get_db().execute(
        "SELECT id, topic, measured_level, created_at FROM stories WHERE student_id = ? ORDER BY id DESC LIMIT 50",
        (g.student["id"],),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


def _record_feedback(story, role: str):
    data = request.get_json(force=True)
    rating, difficulty, flag = data.get("rating"), data.get("difficulty"), data.get("flag")
    if rating is not None and (not isinstance(rating, int) or not 1 <= rating <= 5):
        abort(400, "rating must be 1-5.")
    if difficulty is not None and difficulty not in DIFFICULTY:
        abort(400, f"difficulty must be one of {sorted(DIFFICULTY)}.")
    if flag is not None and flag not in FLAGS:
        abort(400, f"flag must be one of {sorted(FLAGS)}.")
    if rating is None and difficulty is None and flag is None:
        abort(400, "Provide rating, difficulty, or flag.")
    comment, _ = redact(str(data.get("comment") or "")[:500])

    db = get_db()
    sid = story["student_id"]
    db.execute(
        "INSERT INTO feedback (story_id, student_id, author_role, rating, difficulty, flag, comment, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (story["id"], sid, role, rating, difficulty, flag, comment or None, utcnow()),
    )

    student = db.execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
    votes = [r["difficulty"] for r in db.execute(
        "SELECT difficulty FROM feedback WHERE student_id = ? AND difficulty IS NOT NULL ORDER BY id DESC LIMIT ?",
        (sid, RECENT_VOTES))]
    new_level = adjust_level(student["target_level"], votes)
    avoid = loads(student["avoid_topics"])
    if flag == "inappropriate" and story["topic"] not in avoid:
        avoid.append(story["topic"])
    db.execute("UPDATE students SET target_level = ?, avoid_topics = ? WHERE id = ?",
               (new_level, json.dumps(avoid), sid))
    if new_level != student["target_level"]:
        audit(g.actor, "level_adjusted", sid, f"{student['target_level']}->{new_level}")
    db.commit()
    return jsonify({"ok": True, "target_level": new_level}), 201


@bp.post("/<int:story_id>/feedback")
@student_required
def student_feedback(story_id):
    story = get_db().execute(
        "SELECT * FROM stories WHERE id = ? AND student_id = ?", (story_id, g.student["id"])
    ).fetchone()
    if story is None:
        abort(404, "Story not found.")
    return _record_feedback(story, "student")


@bp.post("/<int:story_id>/teacher-feedback")
@teacher_required
def teacher_feedback(story_id):
    story = get_db().execute("SELECT * FROM stories WHERE id = ?", (story_id,)).fetchone()
    if story is None:
        abort(404, "Story not found.")
    teacher_owns_student(story["student_id"])
    return _record_feedback(story, "teacher")

