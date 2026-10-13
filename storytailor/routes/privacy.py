"""Records requests: export, deletion, consent status, and audit trail."""

from flask import Blueprint, abort, g, jsonify, request

from ..auth import teacher_owns_student, teacher_required
from ..db import get_db
from ..privacy import audit, delete_student, export_student

bp = Blueprint("privacy", __name__, url_prefix="/api/students")

CONSENT = {"school_authorized", "pending", "withdrawn"}


@bp.get("/<student_id>/export")
@teacher_required
def export(student_id):
    teacher_owns_student(student_id)
    audit(g.actor, "export_student", student_id)
    get_db().commit()
    return jsonify(export_student(student_id))


@bp.delete("/<student_id>")
@teacher_required
def delete(student_id):
    teacher_owns_student(student_id)
    delete_student(student_id)
    audit(g.actor, "delete_student", student_id)
    get_db().commit()
    return jsonify({"deleted": student_id})


@bp.post("/<student_id>/consent")
@teacher_required
def set_consent(student_id):
    teacher_owns_student(student_id)
    status = (request.get_json(force=True) or {}).get("status")
    if status not in CONSENT:
        abort(400, f"status must be one of {sorted(CONSENT)}.")
    db = get_db()
    db.execute("UPDATE students SET consent_status = ? WHERE id = ?", (status, student_id))
    audit(g.actor, "consent_change", student_id, status)
    db.commit()
    return jsonify({"student_id": student_id, "consent_status": status})


@bp.get("/<student_id>/audit")
@teacher_required
def audit_trail(student_id):
    teacher_owns_student(student_id)
    rows = get_db().execute(
        "SELECT actor, action, detail, created_at FROM audit_log WHERE student_id = ? ORDER BY id",
        (student_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])
