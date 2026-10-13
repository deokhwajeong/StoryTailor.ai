"""Readability estimation.

Uses the Flesch-Kincaid grade formula and maps the grade to an approximate
Lexile-style level using published grade-band midpoints. This is an
approximation for adapting stories, not an official Lexile measure.
"""

import re

# Approximate Lexile-style midpoints by U.S. grade (end-of-year bands).
_GRADE_TO_LEVEL = [
    (0, 100), (1, 300), (2, 500), (3, 640), (4, 780), (5, 880),
    (6, 950), (7, 1010), (8, 1050), (9, 1080), (10, 1120), (12, 1200),
]

_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_SENTENCE_RE = re.compile(r"[.!?]+")


def count_syllables(word: str) -> int:
    word = word.lower()
    if len(word) <= 3:
        return 1
    word = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", word)
    word = re.sub(r"^y", "", word)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", word)))


def fk_grade(text: str) -> tuple[float, int, int]:
    words = _WORD_RE.findall(text)
    sentences = max(1, len([s for s in _SENTENCE_RE.split(text) if s.strip()]))
    if not words:
        return 0.0, 0, sentences
    syllables = sum(count_syllables(w) for w in words)
    grade = 0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59
    return max(0.0, grade), len(words), sentences


def grade_to_level(grade: float) -> int:
    if grade <= _GRADE_TO_LEVEL[0][0]:
        return _GRADE_TO_LEVEL[0][1]
    for (g0, l0), (g1, l1) in zip(_GRADE_TO_LEVEL, _GRADE_TO_LEVEL[1:]):
        if grade <= g1:
            return round(l0 + (l1 - l0) * (grade - g0) / (g1 - g0))
    return _GRADE_TO_LEVEL[-1][1]


def estimate(text: str) -> dict:
    grade, words, sentences = fk_grade(text)
    return {
        "fk_grade": round(grade, 1),
        "approx_level": grade_to_level(grade),
        "words": words,
        "sentences": sentences,
        "method": "flesch-kincaid, mapped to approximate Lexile-style band",
    }
