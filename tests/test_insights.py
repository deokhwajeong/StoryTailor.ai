from datetime import datetime, timedelta, timezone

from storytailor.insights import attention_reasons, needs_attention

NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
RECENT = (NOW - timedelta(days=1)).isoformat(timespec="seconds")


def reasons(**overrides):
    args = {"grade": 3, "target_level": 600, "recent_votes": [], "flags": 0, "last_active_at": RECENT, "now": NOW}
    return attention_reasons(**(args | overrides))


def test_on_track_student_has_no_reasons():
    assert reasons(recent_votes=["just_right", "just_right", "too_easy"]) == []


def test_struggling_and_ready_for_more_follow_vote_majority():
    assert reasons(recent_votes=["too_hard", "too_hard", "just_right"]) == ["struggling"]
    assert reasons(recent_votes=["too_easy", "too_easy"]) == ["ready_for_more"]
    # A single vote is not a trend.
    assert reasons(recent_votes=["too_hard"]) == []
    # Only the most recent five votes count.
    assert reasons(recent_votes=["just_right"] * 5 + ["too_hard"] * 5) == []


def test_below_grade_level_uses_grade_start_minus_margin():
    assert reasons(target_level=450) == ["below_grade_level"]   # grade 3 starts at 600
    assert reasons(target_level=460) == []


def test_inactive_after_fourteen_days_or_never_active():
    assert reasons(last_active_at=(NOW - timedelta(days=15)).isoformat()) == ["inactive"]
    assert reasons(last_active_at=None) == ["inactive"]
    assert reasons(last_active_at=(NOW - timedelta(days=13)).isoformat()) == []


def test_reasons_are_ordered_by_urgency():
    assert reasons(flags=1, target_level=400, recent_votes=["too_hard"] * 3, last_active_at=None) == [
        "flagged_story", "struggling", "below_grade_level", "inactive"]


def test_needs_attention_skips_on_track_and_sorts():
    base = {"grade": 3, "target_level": 600, "recent_votes": [], "flags": 0, "last_active_at": RECENT}
    students = [
        base | {"id": "stu_a"},
        base | {"id": "stu_b", "last_active_at": None},
        base | {"id": "stu_c", "flags": 1, "recent_votes": ["too_hard", "too_hard"]},
        base | {"id": "stu_d", "flags": 1},
    ]
    result = needs_attention(students, NOW)
    assert [r["student_id"] for r in result] == ["stu_c", "stu_d", "stu_b"]
    assert result[0]["reasons"] == ["flagged_story", "struggling"]


def test_feedback_summary_lists_students_needing_attention(client, teacher, classroom, student):
    for _ in range(2):
        sid = client.post("/api/stories", json={"topic": "owls"}, headers=student["headers"]).get_json()["id"]
        client.post(f"/api/stories/{sid}/feedback", json={"difficulty": "too_hard"}, headers=student["headers"])
    summary = client.get(f"/api/classrooms/{classroom['id']}/feedback-summary", headers=teacher).get_json()
    assert summary["needs_attention"] == [
        {"student_id": student["id"], "target_level": 350, "reasons": ["struggling"],
         "recent_votes": ["too_hard", "too_hard"]}]
