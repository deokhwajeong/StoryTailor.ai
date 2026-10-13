"""Story personalization and the classroom feedback loop.

1. Build a prompt from the student's grade, target level, interests, and any
   topics teachers or the student flagged, plus grounding facts.
2. Generate, safety-check, and measure readability. If the story reads well
   above the target, regenerate once with a simplification instruction.
3. After feedback ("too hard" / "too easy"), nudge the target level so the
   next story fits better.
"""

from dataclasses import dataclass, field

from . import readability, safety
from .knowledge import default_kb

LEVEL_STEP = 50
LEVEL_MIN, LEVEL_MAX = 100, 1300
# Starting target by grade when a teacher does not set one.
DEFAULT_LEVEL_BY_GRADE = {0: 150, 1: 300, 2: 450, 3: 600, 4: 740, 5: 840, 6: 920, 7: 980, 8: 1030}


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


def build_prompt(profile: Profile, topic: str, learning_goal: str | None, facts: list[dict],
                 simplify: bool = False) -> tuple[str, str]:
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
    if simplify:
        user += "SIMPLIFY: the last draft was too hard. Use shorter sentences and simpler words.\n"
    return system, user


def generate_story(provider, profile: Profile, topic: str, learning_goal: str | None,
                   tolerance: int) -> dict:
    ok, hits = safety.is_safe(f"{topic} {learning_goal or ''}")
    if not ok:
        raise UnsafeRequest(f"Topic not allowed for this classroom: {', '.join(hits)}")

    facts = default_kb().search(f"{topic} {' '.join(profile.interests)}", k=3)
    attempts = 0
    simplify = False
    while True:
        attempts += 1
        system, user = build_prompt(profile, topic, learning_goal, facts, simplify=simplify)
        text = safety.soften(provider.generate(system, user))
        measured = readability.estimate(text)["approx_level"]
        if measured - profile.target_level <= tolerance or attempts >= 2:
            break
        simplify = True

    ok, hits = safety.is_safe(text)
    if not ok or provider.flagged(text):
        raise UnsafeRequest("Generated story did not pass the safety check. Please try another topic.")

    return {
        "text": text,
        "measured_level": measured,
        "target_level": profile.target_level,
        "sources": [{"id": f["id"], "source": f["source"]} for f in facts],
        "attempts": attempts,
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
