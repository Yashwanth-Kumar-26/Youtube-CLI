"""Thumbnail fetch via httpx + chafa render."""
from __future__ import annotations

import asyncio
import os
import pathlib
import re
import shutil
import tempfile


import httpx


def _available() -> bool:
    return shutil.which("chafa") is not None


async def _download(url: str) -> pathlib.Path | None:
    """Download thumbnail to a temp file. Returns the path or None on failure."""
    try:
        resp = await asyncio.wait_for(_fetch(url), timeout=15.0)
        fd, tmp = tempfile.mkstemp(suffix=".jpg", prefix="yt_thumb_")
        os.write(fd, resp)
        os.close(fd)
        return pathlib.Path(tmp)
    except Exception:
        return None


async def _fetch(url: str) -> bytes:
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _clean_ansi(text: str) -> str:
    """Strip cursor-hide/show and other sequences that break Textual rendering."""
    # Remove hide/show cursor sequences
    text = text.replace("\x1b[?25l", "").replace("\x1b[?25h", "")
    # Remove cursor position save/restore
    text = re.sub(r"\x1b7|\x1b8", "", text)
    # Remove DEC private mode sequences
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
            "chafa", "-f", "symbols", "--symbols", "braille",
            "-s", f"{width}x{width // 2}", str(img),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        result = stdout.decode() if proc.returncode == 0 else ""
        return _clean_ansi(result) if result else ""
    except Exception:
        return ""
    finally:
        if img and img.exists():
            try:
                img.unlink()
            except Exception:
                pass

