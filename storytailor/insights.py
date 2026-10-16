"""Teacher insights: which students may need a check-in, and why.

The rules are deliberately simple and explainable. Each one maps to something a
teacher can act on in a few minutes, and every flag carries its reason so the
dashboard never shows an unexplained score. These are prompts for a human
conversation, not assessments of the child.
"""

from datetime import datetime, timedelta

from .personalization import default_level

# How many recent difficulty votes to look at (same window as level adjustment).
RECENT_VOTES = 5
# Fewer votes than this is not enough signal to call a trend.
MIN_VOTES = 2
INACTIVE_DAYS = 14
# Target level this far below the grade's starting level suggests extra support.
BELOW_GRADE_MARGIN = 150

# Ordered by urgency; the dashboard lists reasons in this order.
REASONS = ("flagged_story", "struggling", "below_grade_level", "inactive", "ready_for_more")


def attention_reasons(*, grade: int, target_level: int, recent_votes: list[str], flags: int,
                      last_active_at: str | None, now: datetime) -> list[str]:
    """Return the reason codes (subset of REASONS, in that order) for one student."""
    reasons = set()
    if flags > 0:
        reasons.add("flagged_story")

    votes = recent_votes[:RECENT_VOTES]
    if len(votes) >= MIN_VOTES:
        hard, easy = votes.count("too_hard"), votes.count("too_easy")
        if hard > easy and hard * 2 >= len(votes):
            reasons.add("struggling")
        elif easy > hard and easy * 2 >= len(votes):
            reasons.add("ready_for_more")

    if target_level <= default_level(grade) - BELOW_GRADE_MARGIN:
        reasons.add("below_grade_level")

    if last_active_at is None or datetime.fromisoformat(last_active_at) < now - timedelta(days=INACTIVE_DAYS):
        reasons.add("inactive")

    return [r for r in REASONS if r in reasons]


def needs_attention(students: list[dict], now: datetime) -> list[dict]:
    """students: dicts with id, grade, target_level, recent_votes, flags, last_active_at.

    Returns only students with at least one reason, most reasons first, then
    by urgency of their top reason, then by id for a stable order.
    """
    out = []
    for s in students:
        reasons = attention_reasons(
            grade=s["grade"], target_level=s["target_level"], recent_votes=s["recent_votes"],
            flags=s["flags"], last_active_at=s["last_active_at"], now=now,
        )
        if reasons:
            out.append({"student_id": s["id"], "target_level": s["target_level"], "reasons": reasons})
    out.sort(key=lambda r: (-len(r["reasons"]), REASONS.index(r["reasons"][0]), r["student_id"]))
    return out
