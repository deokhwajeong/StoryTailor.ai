"""Model providers.

Only redacted, pseudonymous content reaches a provider: the prompt carries a
grade, a target level, interests, and a topic, never a student identifier.
"""

import os
from typing import Protocol

from flask import current_app


class StoryProvider(Protocol):
    def generate(self, system: str, user: str) -> str: ...
    def flagged(self, text: str) -> bool: ...


class OpenAIProvider:
    def __init__(self, model: str):
        from openai import OpenAI

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set (or use STORYTAILOR_LLM_PROVIDER=offline).")
        self.client = OpenAI()
        self.model = model

    def generate(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7,
            max_tokens=900,
            store=False,
        )
        return resp.choices[0].message.content.strip()

    def flagged(self, text: str) -> bool:
        return self.client.moderations.create(model="omni-moderation-latest", input=text).results[0].flagged


class OfflineProvider:
    """Deterministic template generator for demos, tests, and air-gapped classrooms."""

    def generate(self, system: str, user: str) -> str:
        fields = dict(
            line.split(": ", 1) for line in user.splitlines() if ": " in line
        )
        topic = fields.get("Topic", "a new friend")
        goal = fields.get("Learning goal", "be kind")
        simple = "SIMPLIFY" in user
        if simple:
            return (
                f"Mia liked {topic}. One day she had a problem. "
                f"She asked a friend for help. They tried again. "
                f"It worked! Mia learned to {goal}."
            )
        return (
            f"Mia had always wondered about {topic}. On Saturday morning she packed a notebook "
            f"and walked to the library with her friend Leo. They found a book full of pictures "
            f"and read it together under the big window. When a page was hard, they sounded out "
            f"the long words and took turns. By the end of the day Mia had filled three pages "
            f"with drawings, and she understood how to {goal}."
        )

    def flagged(self, text: str) -> bool:
        return False


def make_provider(config) -> StoryProvider:
    if config["LLM_PROVIDER"] == "offline":
        return OfflineProvider()
    return OpenAIProvider(config["OPENAI_MODEL"])


def get_provider() -> StoryProvider:
    """Created on first use so the app starts (and tests run) without an API key."""
    ext = current_app.extensions
    if "story_provider" not in ext:
        ext["story_provider"] = make_provider(current_app.config)
    return ext["story_provider"]
