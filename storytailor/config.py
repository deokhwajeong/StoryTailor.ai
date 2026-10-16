"""Configuration, read from environment variables (see .env.example)."""

import os


class Config:
    SECRET_KEY = os.getenv("STORYTAILOR_SECRET_KEY", "dev-only-change-me")
    DATABASE = os.getenv("STORYTAILOR_DATABASE", "instance/storytailor.sqlite")

    # Story content and feedback older than this are purged by `flask purge-expired`.
    # Default is roughly one school year plus summer.
    RETENTION_DAYS = int(os.getenv("STORYTAILOR_RETENTION_DAYS", "400"))

    # "openai" uses the OpenAI API; "offline" uses a deterministic local generator
    # so the app can be demoed and tested without sending anything off-device.
    LLM_PROVIDER = os.getenv("STORYTAILOR_LLM_PROVIDER", "openai")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]
