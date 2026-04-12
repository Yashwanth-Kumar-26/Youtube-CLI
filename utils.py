"""Shared helpers: formatting, config, safe JSON I/O."""
from __future__ import annotations

import json
from pathlib import Path


# ── Formatting ────────────────────────────────────────────────────────────────

def fmt_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return "--:--"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def fmt_views(count: int | None) -> str:
    if count is None:
        return "N/A"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR = Path.home() / ".yt-cli"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> list | dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(path: Path, data: list | dict) -> None:
    ensure_data_dir()
    path.write_text(json.dumps(data, indent=2))
