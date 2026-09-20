"""Ensure TYPESAFE_API_KEY is present (already in env for this box)."""
from __future__ import annotations

import os


def ensure() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise SystemExit("TYPESAFE_API_KEY not set")
    return key
