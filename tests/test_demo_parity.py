"""Guards against drift between the server and the in-browser demo mock.

The static demo (frontend/frontend/src/demo/) re-implements a few server rules
in TypeScript so it can run with no backend. These tests read that source and
fail if a constant, word list, or sample measurement no longer matches the
Python it claims to mirror.
"""

import json
import re
from pathlib import Path

import pytest

from storytailor import books, insights, personalization, readability, safety
from storytailor.privacy import _PII_PATTERNS
from storytailor.routes.stories import RECENT_VOTES

DEMO = Path(__file__).resolve().parents[1] / "frontend" / "frontend" / "src" / "demo"
MOCK = (DEMO / "mockApi.ts").read_text()
TEACHER = (DEMO / "teacherData.ts").read_text()


def ts_const(source: str, name: str) -> int:
    m = re.search(rf"\bconst {name} = (\d+);", source)
    assert m, f"{name} not found in demo source"
    return int(m.group(1))


def ts_string_list(source: str, name: str) -> list[str]:
    m = re.search(rf"\bconst {name}[^=]*= \[(.*?)\]", source, re.S)
    assert m, f"{name} not found in demo source"
    return re.findall(r"'([^']*)'", m.group(1))


@pytest.mark.parametrize("name,expected", [
    ("LEVEL_STEP", personalization.LEVEL_STEP),
    ("LEVEL_MIN", personalization.LEVEL_MIN),
    ("LEVEL_MAX", personalization.LEVEL_MAX),
    ("RECENT_VOTES", RECENT_VOTES),
    ("BAND_BELOW", books.BAND_BELOW),
    ("BAND_ABOVE", books.BAND_ABOVE),
])
def test_mock_constants_match_server(name, expected):
    assert ts_const(MOCK, name) == expected


@pytest.mark.parametrize("name,expected", [
    ("MIN_VOTES", insights.MIN_VOTES),
    ("INACTIVE_DAYS", insights.INACTIVE_DAYS),
    ("BELOW_GRADE_MARGIN", insights.BELOW_GRADE_MARGIN),
])
def test_teacher_insight_constants_match_server(name, expected):
    assert ts_const(TEACHER, name) == expected


def test_teacher_reason_order_matches_server():
    assert tuple(ts_string_list(TEACHER, "REASONS")) == insights.REASONS


def test_blocklist_matches_server():
    assert ts_string_list(MOCK, "BLOCKED_TERMS") == safety.BLOCKED_TERMS


def test_pii_kinds_match_server_in_order():
    kinds = re.findall(r"\['(\w+)', /", MOCK)
    assert kinds == [kind for kind, _ in _PII_PATTERNS]


def test_sample_story_levels_are_measured_with_server_formula():
    samples = json.loads((DEMO / "stories.json").read_text())
    assert samples, "demo has no sample stories"
    for sample in samples:
        assert set(sample["versions"]) == {"low", "mid", "high"}
        for name, version in sample["versions"].items():
            measured = readability.estimate(version["text"])["approx_level"]
            assert version["measured_level"] == measured, f"{sample['key']}/{name}"


def test_sample_stories_pass_safety_check_and_cite_real_sources():
    knowledge_ids = {k["id"] for k in json.loads(
        (Path(personalization.__file__).parent / "data" / "knowledge.json").read_text())}
    for sample in json.loads((DEMO / "stories.json").read_text()):
        for version in sample["versions"].values():
            assert safety.is_safe(version["text"])[0], sample["key"]
        assert set(sample["sources"]) <= knowledge_ids
