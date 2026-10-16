from storytailor import books, readability
from storytailor.personalization import TRACE_FIELDS

HARD_TEXT = (
    "Notwithstanding considerable environmental variability, cephalopod populations demonstrate "
    "extraordinary physiological adaptability, continuously reconfiguring chromatophore distributions."
)
# Reads at about 400L, inside a grade 2 reader's band (350 to 500L).
MEDIUM_TEXT = (
    "Mia wanted to learn about the moon. On Saturday she went to the library with her friend Leo. "
    "They found a book with big pictures. They read it by the window. "
    "When a word was long, they took turns and sounded it out."
)


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
    resp = client.post("/api/stories", json={"topic": "owls"}, headers={"X-Student-Code": "NOPE1234"})
    assert resp.status_code == 401


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


def drafts_of(data):
    return [s for s in data["trace"] if s["step"] == "draft"]


def test_trace_lists_every_step_in_order_with_known_fields(client, student):
    data = client.post("/api/stories", json={"topic": "octopus", "learning_goal": "keep trying"},
                       headers=student["headers"]).get_json()
    steps = [s["step"] for s in data["trace"]]
    assert steps[:4] == ["shelf", "redaction", "topic_check", "grounding"]
    assert steps[-2:] == ["moderation", "library"]
    assert set(steps[4:-2]) == {"draft"}
    for step in data["trace"]:
        assert set(step) == set(TRACE_FIELDS[step["step"]]), step["step"]
    assert data["trace"][1]["status"] == "clean"
    assert data["trace"][3]["facts"] == data["sources"]


def test_trace_starts_with_shelf_context_for_the_readers_band(client, student):
    data = client.post("/api/stories", json={"topic": "moon"}, headers=student["headers"]).get_json()
    shelf = data["trace"][0]
    assert shelf["band"] == data["band"] == [350, 500]   # grade 2 starts at 450L
    assert shelf["titles"] == books.titles_between(350, 500)
    assert shelf["status"] == ("thin" if shelf["titles"] < books.THIN_SHELF else "ok")


def test_trace_draft_levels_are_measured_with_server_formula(client, student):
    data = client.post("/api/stories", json={"topic": "owls"}, headers=student["headers"]).get_json()
    for draft in drafts_of(data):
        assert draft["band"] == [data["target_level"] - 100, data["target_level"] + 50]
        assert draft["excerpt"]
    accepted = [d for d in drafts_of(data) if d["status"] == "accepted"]
    assert len(accepted) == 1
    assert accepted[0]["measured_level"] == data["measured_level"] == readability.estimate(data["text"])["approx_level"]


def test_too_hard_draft_is_rejected_then_regenerated_draft_accepted(client, student, app):
    provider = app.extensions["story_provider"]
    provider.next_text = HARD_TEXT
    data = client.post("/api/stories", json={"topic": "octopus"}, headers=student["headers"]).get_json()
    first, second = drafts_of(data)
    assert first["status"] == "rejected" and first["fit"] == "too_hard" and first["instruction"] is None
    assert first["measured_level"] == readability.estimate(HARD_TEXT)["approx_level"]
    assert second["status"] == "accepted" and second["fit"] == "in_band" and second["instruction"] == "simplify"
    assert data["fit"] == "in_band"


def test_too_easy_draft_is_regenerated_with_enrich(client, student, app):
    provider = app.extensions["story_provider"]
    prompts, texts = [], iter(["The cat sat. The dog ran. We had fun. It was a good day.", MEDIUM_TEXT])
    provider.generate = lambda system, user: prompts.append(user) or next(texts)
    data = client.post("/api/stories", json={"topic": "moon"}, headers=student["headers"]).get_json()
    first, second = drafts_of(data)
    assert first["fit"] == "too_easy" and first["status"] == "rejected"
    assert second["instruction"] == "enrich" and second["status"] == "accepted"
    assert "ENRICH" in prompts[-1]


def test_when_no_draft_fits_the_closest_is_kept(client, student, app):
    provider = app.extensions["story_provider"]
    texts = iter([HARD_TEXT, "The cat sat. The dog ran. We had fun."])
    provider.generate = lambda system, user: next(texts)
    data = client.post("/api/stories", json={"topic": "moon"}, headers=student["headers"]).get_json()
    drafts = drafts_of(data)
    assert len(drafts) == 2 and [d["fit"] for d in drafts] == ["too_hard", "too_easy"]
    kept = min(drafts, key=lambda d: abs(d["measured_level"] - data["target_level"]))
    assert kept["status"] == "accepted"
    assert data["measured_level"] == kept["measured_level"]


def test_trace_shows_redacted_request_without_the_removed_value(client, student):
    data = client.post("/api/stories", json={"topic": "my name is Ava, owls"},
                       headers=student["headers"]).get_json()
    redaction = data["trace"][1]
    assert redaction == {"step": "redaction", "status": "removed", "kinds": ["name"],
                         "topic": "my name is [name], owls", "learning_goal": None}
    assert "Ava" not in str(data["trace"])


def test_trace_reports_moderation_checks_and_library_books_in_band(client, student):
    data = client.post("/api/stories", json={"topic": "moon"}, headers=student["headers"]).get_json()
    moderation, library = data["trace"][-2], data["trace"][-1]
    assert moderation["checks"] == [{"name": "word_list", "result": "passed"},
                                    {"name": "moderation_service", "result": "not_run"}]
    assert library["books"] and len(library["books"]) <= 3
    lo, hi = library["band"]
    assert all(lo <= b["lexile"] <= hi for b in library["books"])
    assert set(library["books"][0]) == {"id", "title", "lexile", "guided_level"}
