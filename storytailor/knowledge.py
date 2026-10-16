"""Grounding knowledge base.

Stories about real-world topics (animals, space, weather) should not teach
children things that are false. Before generation, the most relevant curated
facts are retrieved with BM25 and placed in the prompt, and the model is told
to use only those facts. Retrieval is pure Python so it runs offline and
needs no vector database for a corpus this size.
"""

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

_TOKEN_RE = re.compile(r"[a-z]+")
_STOPWORDS = {
    "a", "an", "and", "the", "of", "to", "in", "is", "are", "it", "its", "on", "for",
    "with", "that", "this", "as", "be", "can", "so", "or", "by", "at", "they", "their",
    "about", "story", "stories",
}


def tokenize(text: str) -> list[str]:
    tokens = [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]
    # Light stemming so "rabbits" matches "rabbit" and "owls" matches "owl".
    return [t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t for t in tokens]


class KnowledgeBase:
    def __init__(self, docs: list[dict], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.doc_tokens = [tokenize(d["content"] + " " + d["theme"]) for d in docs]
        self.avgdl = sum(map(len, self.doc_tokens)) / max(1, len(docs))
        df = Counter(t for toks in self.doc_tokens for t in set(toks))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = tokenize(query)
        scored = []
        for doc, toks in zip(self.docs, self.doc_tokens, strict=True):
            tf = Counter(toks)
            score = 0.0
            for t in q:
                if t in tf:
                    num = tf[t] * (self.k1 + 1)
                    den = tf[t] + self.k1 * (1 - self.b + self.b * len(toks) / self.avgdl)
                    score += self.idf[t] * num / den
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc | {"score": round(score, 3)} for score, doc in scored[:k]]


@lru_cache(maxsize=1)
def default_kb() -> KnowledgeBase:
    path = Path(__file__).parent / "data" / "knowledge.json"
    return KnowledgeBase(json.loads(path.read_text()))
