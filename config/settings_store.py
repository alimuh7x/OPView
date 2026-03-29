"""
Persistent user settings for OPView stored in ~/.opview_settings.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_SETTINGS_FILE = Path.home() / ".opview_settings.json"


def load() -> dict:
    """Return settings dict, empty dict if file missing or corrupt."""
    try:
        return json.loads(_SETTINGS_FILE.read_text())
    except Exception:
        return {}


def save(data: dict) -> None:
    """Merge data into existing settings and write to disk."""
    current = load()
    current.update(data)
    _SETTINGS_FILE.write_text(json.dumps(current, indent=2))


def apply_env() -> None:
    """
    Copy API keys from settings file into os.environ if not already set.
    Called once at app startup so the AI callback can find the keys.
    """
    settings = load()
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GITHUB_TOKEN"):
        if settings.get(key) and not os.environ.get(key):
            os.environ[key] = settings[key]


def get(key: str, default: str = "") -> str:
    return load().get(key, default)
