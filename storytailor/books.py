"""Classroom library: fuzzy title search and leveled recommendations.

The catalog in data/books.json is the book list a classroom kept for its
digital library search page (title, Lexile, guided reading letter level).
Lexile and letter levels are kept exactly as recorded; they were not
re-verified. Topic tags are keyword guesses from titles, used only to
nudge recommendations toward a student's interests.
"""

import json
from functools import lru_cache
from pathlib import Path

# MetaMetrics' suggested reading range: 100L below to 50L above the reader.
BAND_BELOW, BAND_ABOVE = 100, 50
# Shelf coverage: titles are counted per 100L band, and a band (or a reader's
# own range) with fewer than THIN_SHELF titles is called thin. Most of the
# catalog sits in 500 to 699L, so readers at the edges have few real books.
COVERAGE_BAND = 100
THIN_SHELF = 10


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    return json.loads((Path(__file__).parent / "data" / "books.json").read_text())


@lru_cache(maxsize=1)
def by_id() -> dict[str, dict]:
    return {b["id"]: b for b in catalog()}


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _similarity(query: str, title: str) -> float:
    """Best match of the query against the whole title or any same-length window
    of it, so "wimpy kidd" still finds "Diary of a Wimpy Kid"."""
    title = title.lower()
    n = len(query)
    candidates = [title] + [title[i:i + n] for i in range(0, max(1, len(title) - n + 1))]
    best = min(levenshtein(query, c) for c in candidates)
    return 1 - best / max(n, 1)


def search(query: str = "", guided_level: str | None = None, min_lexile: int | None = None,
           max_lexile: int | None = None, limit: int = 20) -> dict:
    """Substring search with filters; if nothing matches, fall back to the
    closest titles by edit distance (typos are common when kids search)."""
    q = query.strip().lower()

    def passes(b):
        return ((not guided_level or b["guided_level"] == guided_level.upper())
                and (min_lexile is None or b["lexile"] >= min_lexile)
                and (max_lexile is None or b["lexile"] <= max_lexile))

    pool = [b for b in catalog() if passes(b)]
    exact = [b for b in pool if q in b["title"].lower()]
    if exact or not q:
        return {"results": exact[:limit], "fuzzy": False}
    scored = sorted(((_similarity(q, b["title"]), b) for b in pool), key=lambda x: x[0], reverse=True)
    close = [b | {"similarity": round(s, 2)} for s, b in scored[:3] if s >= 0.6]
    return {"results": close, "fuzzy": True}


def recommend(target_level: int, interests: list[str], already_read: set[str], k: int = 5) -> list[dict]:
    """Books in the reader's band, ranked by interest overlap then closeness to target.
    If the band has too few unread books, widen it rather than return nothing."""
    interests = {i.lower() for i in interests}
    unread = [b for b in catalog() if b["id"] not in already_read]
    for widen in (0, 50, 100, 200):
        lo, hi = target_level - BAND_BELOW - widen, target_level + BAND_ABOVE + widen
        band = [b for b in unread if lo <= b["lexile"] <= hi]
        if len(band) >= k:
            break
    ranked = sorted(band, key=lambda b: (-len(interests & set(b["tags"])), abs(b["lexile"] - target_level),
                                         b["title"]))
    return [
        b | {"interest_matches": sorted(interests & set(b["tags"])), "lexile_difference": b["lexile"] - target_level}
        for b in ranked[:k]
    ]


def titles_between(low: int, high: int) -> int:
    """Number of catalog titles with low <= Lexile <= high."""
    return sum(1 for b in catalog() if low <= b["lexile"] <= high)


def shelf_for_reader(target_level: int) -> dict:
    """How many real books sit in this reader's band, and whether that is thin."""
    low, high = target_level - BAND_BELOW, target_level + BAND_ABOVE
    titles = titles_between(low, high)
    return {"band": [low, high], "titles": titles, "thin": titles < THIN_SHELF}


def class_coverage(levels: list[int]) -> dict:
    """Titles per 100L band across the whole catalog, with how many of the given
    readers (target levels) fall in each band. Bands span the catalog and the
    readers, so a reader beyond the shelf still shows up in an empty band."""
    lexiles = [b["lexile"] for b in catalog()]
    first = min(lexiles + levels) // COVERAGE_BAND * COVERAGE_BAND
    last = max(lexiles + levels) // COVERAGE_BAND * COVERAGE_BAND
    bands = []
    for low in range(first, last + 1, COVERAGE_BAND):
        high = low + COVERAGE_BAND - 1
        titles = sum(1 for x in lexiles if low <= x <= high)
        readers = sum(1 for x in levels if low <= x <= high)
        bands.append({"low": low, "high": high, "titles": titles, "readers": readers,
                      "thin": titles < THIN_SHELF})
    return {
        "band_width": COVERAGE_BAND,
        "thin_threshold": THIN_SHELF,
        "total_titles": len(lexiles),
        "bands": bands,
        "readers_in_thin_bands": sum(b["readers"] for b in bands if b["thin"]),
    }
