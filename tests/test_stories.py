def test_generate_story_is_grounded_and_leveled(client, student):
    resp = client.post("/api/stories", json={"topic": "octopus", "learning_goal": "keep trying"},
                       headers=student["headers"])
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["text"]
    assert any(s["id"] == "animals-octopus" for s in data["sources"])
    assert data["target_level"] == 450
    assert isinstance(data["measured_level"], int)


def test_invalid_code_rejected(client):
    assert client.post("/api/stories", json={"topic": "owls"}, headers={"X-Student-Code": "NOPE1234"}).status_code == 401


def test_unsafe_topic_rejected(client, student):
    resp = client.post("/api/stories", json={"topic": "a story about guns"}, headers=student["headers"])
    assert resp.status_code == 422


def test_pii_is_redacted_before_prompt_and_storage(client, student, app):
    resp = client.post("/api/stories",
                       json={"topic": "my name is Ava and my email is ava@example.com, owls"},
                       headers=student["headers"])
    assert resp.status_code == 201
    data = resp.get_json()
    assert "Ava" not in data["topic"] and "ava@example.com" not in data["topic"]
    assert set(data["redacted"]) == {"email", "name"}
    prompts = "\n".join(app.extensions["story_provider"].prompts)
    assert "Ava" not in prompts and "@" not in prompts
    assert student["id"] not in prompts


def test_too_hard_story_is_regenerated_once(client, student, app):
    provider = app.extensions["story_provider"]
    provider.next_text = (
        "Notwithstanding considerable environmental variability, cephalopod populations demonstrate "
        "extraordinary physiological adaptability, continuously reconfiguring chromatophore distributions."
    )
    data = client.post("/api/stories", json={"topic": "octopus"}, headers=student["headers"]).get_json()
    assert data["attempts"] == 2
    assert "SIMPLIFY" in provider.prompts[-1]


def test_feedback_adjusts_level(client, student):
    level = 450
    for _ in range(2):
        sid = client.post("/api/stories", json={"topic": "moon"}, headers=student["headers"]).get_json()["id"]
        resp = client.post(f"/api/stories/{sid}/feedback", json={"difficulty": "too_easy"},
                           headers=student["headers"])
        assert resp.status_code == 201
        assert resp.get_json()["target_level"] == level + 50
        level += 50


def test_inappropriate_flag_adds_avoid_topic(client, student, teacher):
    sid = client.post("/api/stories", json={"topic": "storms"}, headers=student["headers"]).get_json()["id"]
    client.post(f"/api/stories/{sid}/feedback", json={"flag": "inappropriate"}, headers=student["headers"])
    export = client.get(f"/api/students/{student['id']}/export", headers=teacher).get_json()
    assert "storms" in export["student"]["avoid_topics"]


def test_cannot_give_feedback_on_someone_elses_story(client, teacher, classroom, student):
    sid = client.post("/api/stories", json={"topic": "moon"}, headers=student["headers"]).get_json()["id"]
    other = client.post(f"/api/classrooms/{classroom['id']}/students", json={"count": 1},
                        headers=teacher).get_json()["students"][0]
    resp = client.post(f"/api/stories/{sid}/feedback", json={"rating": 1},
                       headers={"X-Student-Code": other["access_code"]})
    assert resp.status_code == 404
