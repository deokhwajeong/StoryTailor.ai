import pytest

from storytailor import create_app, db
from storytailor.llm import OfflineProvider
from storytailor.privacy import hash_secret

TEACHER_TOKEN = "teacher-token-for-tests"


class RecordingProvider(OfflineProvider):
    """Offline provider that records prompts so tests can assert nothing identifying leaks."""

    def __init__(self):
        self.prompts = []
        self.next_text = None

    def generate(self, system, user):
        self.prompts.append(system + "\n" + user)
        if self.next_text is not None:
            text, self.next_text = self.next_text, None
            return text
        return super().generate(system, user)


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.sqlite"),
        "SECRET_KEY": "test",
        "LLM_PROVIDER": "offline",
    })
    app.extensions["story_provider"] = RecordingProvider()
    with app.app_context():
        db.init_db()
        conn = db.get_db()
        conn.execute("INSERT INTO teachers (display_name, token_hash, created_at) VALUES (?, ?, ?)",
                     ("Room 12", hash_secret(TEACHER_TOKEN), db.utcnow()))
        conn.execute("INSERT INTO teachers (display_name, token_hash, created_at) VALUES (?, ?, ?)",
                     ("Other", hash_secret("other-token"), db.utcnow()))
        conn.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def teacher():
    return {"Authorization": f"Bearer {TEACHER_TOKEN}"}


@pytest.fixture
def classroom(client, teacher):
    return client.post("/api/classrooms", json={"name": "Grade 2", "grade": 2}, headers=teacher).get_json()


@pytest.fixture
def student(client, teacher, classroom):
    resp = client.post(f"/api/classrooms/{classroom['id']}/students",
                       json={"count": 1, "interests": ["ocean"]}, headers=teacher)
    s = resp.get_json()["students"][0]
    return {"id": s["student_id"], "headers": {"X-Student-Code": s["access_code"]}}
