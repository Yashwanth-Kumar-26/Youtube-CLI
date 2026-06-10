"""Shared helpers: formatting, config, safe JSON I/O."""
from __future__ import annotations

import json
import logging
import os
import pathlib
import sys
from pathlib import Path


# ── Cross-platform paths ───────────────────────────────────────

def _platform_data_dir() -> pathlib.Path:
    """Return the platform-appropriate directory for persistent app data.

    - Linux/macOS: ~/.yt-tui
    - Windows:     %APPDATA%/yt-tui
    """
    if sys.platform == "win32":
        return pathlib.Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "yt-tui"
    return Path.home() / ".yt-tui"


def _platform_cache_dir() -> pathlib.Path:
    """Return the platform-appropriate directory for disposable cache data.

    - Linux/macOS: ~/.cache/yt-tui
    - Windows:     %LOCALAPPDATA%/yt-tui/cache
    """
    if sys.platform == "win32":
        return pathlib.Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "yt-tui" / "cache"
    return Path.home() / ".cache" / "yt-tui"


logger = logging.getLogger(__name__)

DATA_DIR = _platform_data_dir()
CACHE_DIR = _platform_cache_dir()

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


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> list | dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.warning("Corrupt JSON file, resetting: %s", path)
        return []


def save_json(path: Path, data: list | dict) -> None:
    ensure_data_dir()
    path.write_text(json.dumps(data, indent=2))


# ── History ───────────────────────────────────────────────────────────────────

class HistoryManager:
    """Persistent search and watch history with in-memory caching.

    Reads are served from an in-memory cache (lazily loaded on first access).
    Writes flush to disk immediately for crash safety.
    """

    _search_cache: list[dict] | None = None
    _watch_cache: list[dict] | None = None

    @classmethod
    def _search_hist_file(cls) -> Path:
        return DATA_DIR / "search_history.json"

    @classmethod
    def _watch_hist_file(cls) -> Path:
        return DATA_DIR / "watch_history.json"

    @classmethod
    def get_search_history(cls) -> list[dict]:
        if cls._search_cache is None:
            cls._search_cache = load_json(cls._search_hist_file())
        return cls._search_cache

    @classmethod
    def add_search(cls, query: str) -> None:
        import datetime
        history = cls.get_search_history()
        # Remove if already exists to move to top
        history[:] = [h for h in history if h["query"] != query]
        history.insert(0, {
            "query": query,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        cls._search_cache = history[:50]  # Keep last 50
        save_json(cls._search_hist_file(), cls._search_cache)

    @classmethod
    def get_watch_history(cls) -> list[dict]:
        if cls._watch_cache is None:
            cls._watch_cache = load_json(cls._watch_hist_file())
        return cls._watch_cache

    @classmethod
    def add_watch(cls, video_data: dict) -> None:
        import datetime
        history = cls.get_watch_history()
        # Remove if already exists
        history[:] = [h for h in history if h["id"] != video_data["id"]]
        video_data["watched_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        history.insert(0, video_data)
        cls._watch_cache = history[:100]  # Keep last 100
        save_json(cls._watch_hist_file(), cls._watch_cache)
