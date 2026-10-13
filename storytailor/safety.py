"""Child-safety checks for topics and generated stories.

Two layers: a fast local word list (always on) and, when the OpenAI provider is
configured, the provider's moderation endpoint. Word matching uses word
boundaries so "award" or "toward" do not trip the "war" rule.
"""

import re

BLOCKED_TERMS = [
    "kill", "killed", "killing", "murder", "blood", "bloody", "gun", "guns", "knife",
    "weapon", "drug", "drugs", "alcohol", "beer", "wine", "cigarette", "vape",
    "war", "suicide", "horror", "gore", "sexy", "dead body",
]

SOFTEN = {
    "kill": "stop",
    "killed": "stopped",
    "scary": "mysterious",
    "terrifying": "surprising",
    "horror": "suspense",
    "blood": "red paint",
}

_BLOCKED_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in BLOCKED_TERMS) + r")\b", re.IGNORECASE)
_SOFTEN_RE = re.compile(r"\b(" + "|".join(SOFTEN) + r")\b", re.IGNORECASE)


def find_blocked(text: str) -> list[str]:
    return sorted({m.group(1).lower() for m in _BLOCKED_RE.finditer(text)})


def is_safe(text: str) -> tuple[bool, list[str]]:
    hits = find_blocked(text)
    return not hits, hits


def soften(text: str) -> str:
    def repl(m: re.Match) -> str:
        word = SOFTEN[m.group(1).lower()]
        return word.capitalize() if m.group(1)[0].isupper() else word
    return _SOFTEN_RE.sub(repl, text)
