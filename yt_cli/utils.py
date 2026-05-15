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


# ── History ───────────────────────────────────────────────────────────────────

class HistoryManager:
    @classmethod
    def _search_hist_file(cls) -> Path:
        return DATA_DIR / "search_history.json"

    @classmethod
    def _watch_hist_file(cls) -> Path:
        return DATA_DIR / "watch_history.json"

    @classmethod
    def get_search_history(cls) -> list[dict]:
        return load_json(cls._search_hist_file())

    @classmethod
    def add_search(cls, query: str) -> None:
        import datetime
        history = cls.get_search_history()
        # Remove if already exists to move to top
        history = [h for h in history if h["query"] != query]
        history.insert(0, {
            "query": query,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        save_json(cls._search_hist_file(), history[:50]) # Keep last 50

    @classmethod
    def get_watch_history(cls) -> list[dict]:
        return load_json(cls._watch_hist_file())

    @classmethod
    def add_watch(cls, video_data: dict) -> None:
        import datetime
        history = cls.get_watch_history()
        # Remove if already exists
        history = [h for h in history if h["id"] != video_data["id"]]
        video_data["watched_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        history.insert(0, video_data)
        save_json(cls._watch_hist_file(), history[:100]) # Keep last 100
