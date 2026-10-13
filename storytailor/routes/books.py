"""Classroom library: search, recommendations, and the student reading log."""

from flask import Blueprint, abort, g, jsonify, request

from .. import books
from ..auth import student_required
from ..db import get_db, loads, utcnow

bp = Blueprint("books", __name__, url_prefix="/api/books")


def _int_arg(name):
    value = request.args.get(name)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        abort(400, f"{name} must be an integer.")


@bp.get("/search")
def search():
    return jsonify(books.search(
        request.args.get("q", ""), request.args.get("level") or None,
        _int_arg("min_lexile"), _int_arg("max_lexile"), min(_int_arg("limit") or 20, 50),
    ))


@bp.get("/recommendations")
@student_required
def recommendations():
    read = {r["book_id"] for r in get_db().execute(
        "SELECT book_id FROM reading_log WHERE student_id = ?", (g.student["id"],))}
    return jsonify({
        "target_level": g.student["target_level"],
        "band": [g.student["target_level"] - books.BAND_BELOW, g.student["target_level"] + books.BAND_ABOVE],
        "books": books.recommend(g.student["target_level"], loads(g.student["interests"]), read,
                                 k=min(_int_arg("k") or 5, 20)),
    })


@bp.post("/log")
@student_required
def log_reading():
    data = request.get_json(force=True)
    book_id, minutes, rating = data.get("book_id"), data.get("minutes"), data.get("rating")
    if book_id not in books.by_id():
        abort(400, "Unknown book_id.")
    if minutes is not None and (not isinstance(minutes, int) or not 1 <= minutes <= 240):
        abort(400, "minutes must be 1-240.")
    if rating is not None and (not isinstance(rating, int) or not 1 <= rating <= 5):
        abort(400, "rating must be 1-5.")
    db = get_db()
    db.execute(
        "INSERT INTO reading_log (student_id, book_id, minutes, completed, rating, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (g.student["id"], book_id, minutes, int(bool(data.get("completed", True))), rating, utcnow()),
    )
    db.commit()
    return jsonify({"ok": True}), 201
