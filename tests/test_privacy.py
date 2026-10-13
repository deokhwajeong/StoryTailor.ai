from datetime import datetime, timedelta, timezone

from storytailor.privacy import purge_expired, redact


def test_redact_patterns():
    text, kinds = redact("Call 408-555-0199 or visit https://x.com, I live at 123 Main St. id 9876543")
    assert "408" not in text and "x.com" not in text and "Main" not in text and "9876543" not in text
    assert set(kinds) == {"phone", "url", "address", "id_number"}


def test_redact_leaves_normal_text():
    text, kinds = redact("The brave owl flew over 3 tall trees.")
    assert kinds == [] and text == "The brave owl flew over 3 tall trees."


def test_export_and_delete(client, teacher, student):
    client.post("/api/stories", json={"topic": "rainbows"}, headers=student["headers"])
    export = client.get(f"/api/students/{student['id']}/export", headers=teacher).get_json()
    assert export["student"]["id"] == student["id"]
    assert len(export["stories"]) == 1

    assert client.delete(f"/api/students/{student['id']}", headers=teacher).status_code == 200
    assert client.post("/api/stories", json={"topic": "x"}, headers=student["headers"]).status_code == 401
    audit = client.get(f"/api/students/{student['id']}/audit", headers=teacher)
    assert audit.status_code == 404  # student is gone; audit rows remain in the table for the district


def test_withdrawn_consent_blocks_access(client, teacher, student):
    client.post(f"/api/students/{student['id']}/consent", json={"status": "withdrawn"}, headers=teacher)
    assert client.post("/api/stories", json={"topic": "owls"}, headers=student["headers"]).status_code == 403


def test_other_teacher_cannot_export(client, student):
    resp = client.get(f"/api/students/{student['id']}/export", headers={"Authorization": "Bearer other-token"})
    assert resp.status_code == 404


def test_purge_expired(app, client, teacher, student):
    client.post("/api/stories", json={"topic": "owls"}, headers=student["headers"])
    old = (datetime.now(timezone.utc) - timedelta(days=500)).isoformat(timespec="seconds")
    with app.app_context():
        from storytailor.db import get_db
        get_db().execute("UPDATE stories SET created_at = ?", (old,))
        get_db().commit()
        result = purge_expired(400)
    assert result["stories"] == 1


def test_audit_trail_records_access(client, teacher, student):
    client.get(f"/api/students/{student['id']}/export", headers=teacher)
    actions = [r["action"] for r in client.get(f"/api/students/{student['id']}/audit", headers=teacher).get_json()]
    assert actions[:2] == ["create_student", "export_student"]


def test_responses_not_cached(client):
    assert client.get("/health").headers["Cache-Control"] == "no-store"
