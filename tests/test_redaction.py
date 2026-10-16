"""PII redaction edge cases: what a child might actually type into a topic box."""

import pytest

from storytailor.privacy import redact


@pytest.mark.parametrize("text,kind,leaked", [
    ("email me at sam.lee+1@example.org please", "email", "sam.lee"),
    ("go to www.example.com for games", "url", "example.com"),
    ("my mom's phone is (408) 555-0199", "phone", "555-0199"),
    ("call +1 408.555.0199", "phone", "555"),
    ("I live at 42 Maple Leaf Lane", "address", "Maple"),
    ("my student number is 20261234", "id_number", "20261234"),
    ("My name is Jordan and I like owls", "name", "Jordan"),
    ("i'm called riley", "name", "riley"),
])
def test_each_pii_kind_is_removed(text, kind, leaked):
    out, kinds = redact(text)
    assert kind in kinds
    assert leaked not in out


def test_name_redaction_keeps_the_lead_in():
    assert redact("my name is Ava, tell me about owls") == ("my name is [name], tell me about owls", ["name"])


def test_email_is_not_double_counted_as_url():
    out, kinds = redact("ava@example.com")
    assert (out, kinds) == ("[email]", ["email"])


@pytest.mark.parametrize("text", [
    "a dragon who is 1000 years old",       # short numbers are allowed
    "the year 2026 on the Moon",
    "an owl named Hoot who loves puzzles",  # fictional character names are fine
    "Room 12 reads about whales",
])
def test_ordinary_story_requests_are_untouched(text):
    assert redact(text) == (text, [])


def test_nothing_identifying_reaches_the_stored_story(client, teacher, student):
    client.post("/api/stories", json={"topic": "owls", "learning_goal": "call me at 408-555-0199"},
                headers=student["headers"])
    export = client.get(f"/api/students/{student['id']}/export", headers=teacher).get_json()
    assert "555" not in export["stories"][0]["learning_goal"]
    audit = client.get(f"/api/students/{student['id']}/audit", headers=teacher).get_json()
    redacted = [r for r in audit if r["action"] == "redacted_input"]
    assert redacted and redacted[0]["detail"] == "phone"
    assert "555" not in str(audit)
