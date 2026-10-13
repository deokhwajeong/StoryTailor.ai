def test_requires_teacher_token(client):
    assert client.post("/api/classrooms", json={"name": "x", "grade": 2}).status_code == 401


def test_create_students_returns_codes_once(client, teacher, classroom, app):
    resp = client.post(f"/api/classrooms/{classroom['id']}/students", json={"count": 3}, headers=teacher)
    assert resp.status_code == 201
    students = resp.get_json()["students"]
    assert len(students) == 3
    assert all(s["student_id"].startswith("stu_") and len(s["access_code"]) == 8 for s in students)

    listing = client.get(f"/api/classrooms/{classroom['id']}/students", headers=teacher).get_json()
    assert "access_code" not in listing[0]
    with app.app_context():
        from storytailor.db import get_db
        stored = [r[0] for r in get_db().execute("SELECT access_code_hash FROM students")]
    assert not any(s["access_code"] in stored for s in students)


def test_batch_limit(client, teacher, classroom):
    resp = client.post(f"/api/classrooms/{classroom['id']}/students", json={"count": 500}, headers=teacher)
    assert resp.status_code == 400


def test_other_teacher_cannot_see_classroom(client, classroom):
    other = {"Authorization": "Bearer other-token"}
    assert client.get(f"/api/classrooms/{classroom['id']}/students", headers=other).status_code == 404


def test_feedback_summary(client, teacher, classroom, student):
    sid = client.post("/api/stories", json={"topic": "tide pools"}, headers=student["headers"]).get_json()["id"]
    client.post(f"/api/stories/{sid}/feedback", json={"rating": 4, "difficulty": "too_hard"},
                headers=student["headers"])
    client.post(f"/api/stories/{sid}/teacher-feedback", json={"flag": "inaccurate", "comment": "check facts"},
                headers=teacher)
    summary = client.get(f"/api/classrooms/{classroom['id']}/feedback-summary", headers=teacher).get_json()
    assert summary["difficulty"]["too_hard"] == 1
    assert summary["rating"] == {"average": 4.0, "count": 1}
    assert summary["flags"][0]["flag"] == "inaccurate"
