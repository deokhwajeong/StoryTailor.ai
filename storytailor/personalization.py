"""Story personalization and the classroom feedback loop.

1. Build a prompt from the student's grade, target level, interests, and any
   topics teachers or the student flagged, plus grounding facts.
2. Generate, measure readability, and compare with the reader's band (the
   same band the library uses). A draft outside the band is rejected and
   regenerated once with a "simplify" or "enrich" instruction; if neither
   draft lands in the band, the closer one is kept. Then safety-check it.
3. After feedback ("too hard" / "too easy"), nudge the target level so the
   next story fits better.
"""

from dataclasses import dataclass, field

from . import books, readability, safety
from .knowledge import default_kb

LEVEL_STEP = 50
LEVEL_MIN, LEVEL_MAX = 100, 1300
# Starting target by grade when a teacher does not set one.
DEFAULT_LEVEL_BY_GRADE = {0: 150, 1: 300, 2: 450, 3: 600, 4: 740, 5: 840, 6: 920, 7: 980, 8: 1030}
# One draft plus one regeneration keeps latency and cost bounded.
MAX_ATTEMPTS = 2
EXCERPT_CHARS = 160

# Field names of each step in the "How this story was made" trace returned with
# a story. The demo mirrors these in frontend/frontend/src/types.ts, and
# tests/test_demo_parity.py fails if the two drift.
TRACE_FIELDS = {
    "shelf": ("step", "status", "band", "titles", "thin_threshold"),
    "redaction": ("step", "status", "kinds", "topic", "learning_goal"),
    "topic_check": ("step", "status", "word_list_size"),
    "grounding": ("step", "status", "facts"),
    "draft": ("step", "status", "attempt", "instruction", "measured_level", "fk_grade", "words",
              "band", "fit", "excerpt"),
    "moderation": ("step", "status", "checks"),
    "library": ("step", "status", "band", "books"),
}


class UnsafeRequest(ValueError):
    pass


@dataclass
class Profile:
    grade: int
    target_level: int
    interests: list[str] = field(default_factory=list)
    avoid_topics: list[str] = field(default_factory=list)


def default_level(grade: int) -> int:
    return DEFAULT_LEVEL_BY_GRADE.get(grade, 1030 if grade > 8 else 150)


def level_band(target_level: int) -> tuple[int, int]:
    """The reader's band: 100L below to 50L above target, as for library books."""
    return target_level - books.BAND_BELOW, target_level + books.BAND_ABOVE


def level_fit(measured: int, band: tuple[int, int]) -> str:
    if measured > band[1]:
        return "too_hard"
    if measured < band[0]:
        return "too_easy"
    return "in_band"


def excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def build_prompt(profile: Profile, topic: str, learning_goal: str | None, facts: list[dict],
                 retry: str | None = None) -> tuple[str, str]:
    fact_lines = "\n".join(f"- {f['content']}" for f in facts) or "- (no reference facts; keep the story fictional)"
    avoid = ", ".join(profile.avoid_topics) or "none"
    system = (
        "You write short, warm, original stories for elementary students.\n"
        f"Reader: grade {profile.grade}, target reading level about {profile.target_level}L "
        "(Lexile-style scale).\n"
        "Rules:\n"
        "- Match the target level: short sentences and common words for lower levels.\n"
        "- Any real-world fact must come from the reference facts below. Do not invent facts.\n"
        "- No violence, weapons, romance, brand names, or scary content.\n"
        f"- Do not include these topics: {avoid}.\n"
        "- 150 to 300 words. End with a clear, kind resolution.\n\n"
        f"Reference facts:\n{fact_lines}"
    )
    user = f"Topic: {topic}\n"
    if profile.interests:
        user += f"Reader interests: {', '.join(profile.interests)}\n"
    user += f"Learning goal: {learning_goal or 'enjoy reading'}\n"
    if retry == "simplify":
        user += "SIMPLIFY: the last draft was too hard. Use shorter sentences and simpler words.\n"
    elif retry == "enrich":
        user += "ENRICH: the last draft was too easy. Use some longer sentences and richer words.\n"
    return system, user


def generate_story(provider, profile: Profile, topic: str, learning_goal: str | None) -> dict:
    """Generate one story and a step-by-step trace of how it was made.

    The trace records only what the pipeline decided (check results, measured
    levels, which draft was kept). It never contains removed personal details.
    """
    trace = []
    ok, hits = safety.is_safe(f"{topic} {learning_goal or ''}")
    if not ok:
        raise UnsafeRequest(f"Topic not allowed for this classroom: {', '.join(hits)}")
    trace.append({"step": "topic_check", "status": "passed", "word_list_size": len(safety.BLOCKED_TERMS)})

    facts = default_kb().search(f"{topic} {' '.join(profile.interests)}", k=3)
    sources = [{"id": f["id"], "source": f["source"]} for f in facts]
    trace.append({"step": "grounding", "status": "found" if facts else "none", "facts": sources})

    band = level_band(profile.target_level)
    drafts = []
    retry = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        system, user = build_prompt(profile, topic, learning_goal, facts, retry=retry)
        text = safety.soften(provider.generate(system, user))
        est = readability.estimate(text)
        fit = level_fit(est["approx_level"], band)
        drafts.append({"text": text, "attempt": attempt, "instruction": retry, "est": est, "fit": fit})
        if fit == "in_band":
            break
        retry = "simplify" if fit == "too_hard" else "enrich"

    # The first draft in the band wins; otherwise keep the one closest to target.
    kept = next((d for d in drafts if d["fit"] == "in_band"), None) or min(
        drafts, key=lambda d: abs(d["est"]["approx_level"] - profile.target_level))
    for d in drafts:
        trace.append({
            "step": "draft",
            "status": "accepted" if d is kept else "rejected",
            "attempt": d["attempt"],
            "instruction": d["instruction"],
            "measured_level": d["est"]["approx_level"],
            "fk_grade": d["est"]["fk_grade"],
            "words": d["est"]["words"],
            "band": list(band),
            "fit": d["fit"],
            "excerpt": excerpt(d["text"]),
        })

    text = kept["text"]
    ok, hits = safety.is_safe(text)
    service = getattr(provider, "moderation_service", False)
    if not ok or provider.flagged(text):
        raise UnsafeRequest("Generated story did not pass the safety check. Please try another topic.")
    trace.append({"step": "moderation", "status": "passed", "checks": [
        {"name": "word_list", "result": "passed"},
        {"name": "moderation_service", "result": "passed" if service else "not_run"},
    ]})

    return {
        "text": text,
        "measured_level": kept["est"]["approx_level"],
        "target_level": profile.target_level,
        "band": list(band),
        "fit": kept["fit"],
        "sources": sources,
        "attempts": len(drafts),
        "trace": trace,
    }


def adjust_level(current: int, recent_difficulty: list[str]) -> int:
    """Move one step toward the reader based on the last few difficulty votes."""
    if not recent_difficulty:
        return current
    hard = recent_difficulty.count("too_hard")
    easy = recent_difficulty.count("too_easy")
    if hard > easy and hard * 2 >= len(recent_difficulty):
        current -= LEVEL_STEP
    elif easy > hard and easy * 2 >= len(recent_difficulty):
        current += LEVEL_STEP
    return max(LEVEL_MIN, min(LEVEL_MAX, current))
