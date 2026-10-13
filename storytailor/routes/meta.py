"""Public endpoints that store nothing."""

from flask import Blueprint, abort, jsonify, request

from .. import readability
from ..knowledge import default_kb

bp = Blueprint("meta", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/api/readability")
def estimate_readability():
    """Estimate the level of any passage (e.g. a book page a teacher is considering).
    The text is analyzed in memory and not stored."""
    text = str((request.get_json(force=True) or {}).get("text", ""))
    if not text.strip():
        abort(400, "text is required.")
    return jsonify(readability.estimate(text[:20000]))


@bp.get("/api/knowledge/search")
def search_knowledge():
    q = request.args.get("q", "")
    return jsonify(default_kb().search(q, k=min(int(request.args.get("k", 3)), 10)))
