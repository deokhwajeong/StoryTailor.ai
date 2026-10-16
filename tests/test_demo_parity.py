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
from storytailor.routes.stories import RECENT_VOTES, STORY_BOOKS

DEMO = Path(__file__).resolve().parents[1] / "frontend" / "frontend" / "src" / "demo"
MOCK = (DEMO / "mockApi.ts").read_text()
TEACHER = (DEMO / "teacherData.ts").read_text()
TYPES = (DEMO.parent / "types.ts").read_text()


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
    ("MAX_ATTEMPTS", personalization.MAX_ATTEMPTS),
    ("EXCERPT_CHARS", personalization.EXCERPT_CHARS),
    ("STORY_BOOKS", STORY_BOOKS),
    ("COVERAGE_BAND", books.COVERAGE_BAND),
    ("THIN_SHELF", books.THIN_SHELF),
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
            est = readability.estimate(version["text"])
            assert version["measured_level"] == est["approx_level"], f"{sample['key']}/{name}"
            assert version["fk_grade"] == est["fk_grade"], f"{sample['key']}/{name}"
            assert version["words"] == est["words"], f"{sample['key']}/{name}"


def test_sample_stories_pass_safety_check_and_cite_real_sources():
    knowledge_ids = {k["id"] for k in json.loads(
        (Path(personalization.__file__).parent / "data" / "knowledge.json").read_text())}
    for sample in json.loads((DEMO / "stories.json").read_text()):
        for version in sample["versions"].values():
            assert safety.is_safe(version["text"])[0], sample["key"]
        assert set(sample["sources"]) <= knowledge_ids


def ts_interface_fields(name: str) -> tuple[str, ...]:
    m = re.search(rf"export interface {name} \{{(.*?)\n\}}", TYPES, re.S)
    assert m, f"{name} not found in types.ts"
    return tuple(re.findall(r"^\s+(\w+)\??:", m.group(1), re.M))


@pytest.mark.parametrize("step,interface", [
    ("shelf", "TraceShelf"),
    ("redaction", "TraceRedaction"),
    ("topic_check", "TraceTopicCheck"),
    ("grounding", "TraceGrounding"),
    ("draft", "TraceDraft"),
    ("moderation", "TraceModeration"),
    ("library", "TraceLibrary"),
])
def test_trace_step_shape_matches_server(step, interface):
    # The mock is typed against these interfaces, so tsc keeps the mock in line
    # with types.ts and this test keeps types.ts in line with the server.
    assert ts_interface_fields(interface) == personalization.TRACE_FIELDS[step]
    assert re.search(rf"step: '{step}';", TYPES)


def test_mock_builds_every_trace_step_in_server_order():
    block = re.search(r"const trace: TraceStep\[\] = \[(.*?)\n  \];", MOCK, re.S)
    assert block, "trace array not found in mockApi.ts"
    steps = re.findall(r"step: '(\w+)'|\.\.\.(draftSteps)", block.group(1))
    order = ["draft" if b else a for a, b in steps]
    assert order == ["shelf", "redaction", "topic_check", "grounding", "draft", "moderation", "library"]


def test_demo_drafts_land_on_both_sides_of_a_default_band():
    """The demo's first draft at the grade 3 start level is rejected as too hard for
    every topic and the regenerated draft is in the band, using real measurements."""
    lo, hi = personalization.level_band(personalization.default_level(3))
    for sample in json.loads((DEMO / "stories.json").read_text()):
        levels = sorted(v["measured_level"] for v in sample["versions"].values())
        assert levels[-1] > hi, sample["key"]
        assert any(lo <= lv <= hi for lv in levels[:-1]), sample["key"]


def test_library_coverage_shape_matches_server():
    cov = books.class_coverage([600])
    assert ts_interface_fields("LibraryCoverage") == tuple(cov)
    assert ts_interface_fields("CoverageBand") == tuple(cov["bands"][0])
    assert "library_coverage: classCoverage(" in MOCK
