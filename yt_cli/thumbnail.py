"""Thumbnail fetch via httpx + chafa render with on-disk cache."""
from __future__ import annotations

import asyncio
import hashlib
import pathlib
import re
import shutil

import httpx


CACHE_DIR = pathlib.Path.home() / ".cache" / "yt-cli" / "thumbnails"


def _available() -> bool:
    return shutil.which("chafa") is not None


def _cache_path(url: str) -> pathlib.Path:
    h = hashlib.sha256(url.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{h}.jpg"


async def _download(url: str) -> pathlib.Path | None:
    """Download thumbnail to cache or return cached path."""
    cached = _cache_path(url)
    if cached.exists() and cached.stat().st_size > 0:
        return cached
    try:
        resp = await asyncio.wait_for(_fetch(url), timeout=15.0)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(resp)
        return cached
    except Exception:
        return None


async def _fetch(url: str) -> bytes:
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _clean_ansi(text: str) -> str:
    """Strip sequences that break Textual rendering."""
    text = text.replace("\x1b[?25l", "").replace("\x1b[?25h", "")
    text = re.sub(r"\x1b7|\x1b8", "", text)
    text = re.sub(r"\x1b\[\??[0-9;]*[hl]", "", text)
    return text


async def render(url: str, width: int = 36) -> str:
    if not url or not _available():
        return ""
    img = None
    try:
        img = await _download(url)
        if not img or not img.exists():
            return ""

        proc = await asyncio.create_subprocess_exec(
            "chafa",
            "-s", f"{width}x{width // 2}", str(img),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        result = stdout.decode() if proc.returncode == 0 else ""
        return _clean_ansi(result) if result else ""
    except Exception:
        return ""

