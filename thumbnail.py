"""Thumbnail fetch via curl + chafa render."""
from __future__ import annotations

import asyncio
import pathlib
import shutil
import subprocess
import tempfile


def _available() -> bool:
    return shutil.which("chafa") is not None and shutil.which("curl") is not None


async def _download(url: str) -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp()) / "thumb.jpg"
    proc = await asyncio.create_subprocess_exec(
        "curl", "-sSL", url, "-o", str(tmp)
    )
    await proc.wait()
    return tmp


async def render(url: str, width: int = 36) -> str:
    if not url or not _available():
        return ""
    img = None
    try:
        img = await _download(url)
        proc = await asyncio.create_subprocess_exec(
            "chafa", "-f", "symbols", "-s", f"{width}x{width // 2}", str(img),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode() if proc.returncode == 0 else ""
    except Exception:
        return ""
    finally:
        try:
            if img and img.exists():
                img.unlink()
                if img.parent.exists():
                    img.parent.rmdir()
        except Exception:
            pass

