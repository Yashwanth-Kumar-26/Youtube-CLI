"""mpv subprocess wrapper."""
from __future__ import annotations

import shutil
import subprocess
import sys


def _check_mpv() -> None:
    if not shutil.which("mpv"):
        distro_hint = (
            "  Fedora : sudo dnf install mpv\n"
            "  Ubuntu : sudo apt install mpv\n"
            "  Arch   : sudo pacman -S mpv"
        )
        print(f"[yt-cli] mpv not found. Install it first:\n{distro_hint}", file=sys.stderr)
        sys.exit(1)


def play(url: str, audio_only: bool = False) -> None:
    """Spawn mpv for *url*, blocking until the user quits.

    Raises RuntimeError if mpv exits with a non-zero code (other than
    the normal user-quit code 4).
    """
    _check_mpv()
    cmd = ["mpv", "--really-quiet", url]
    if audio_only:
        cmd.append("--no-video")
    result = subprocess.run(cmd)
    # mpv exit code 4 = user quit (q key) — treat as success
    if result.returncode not in (0, 4):
        raise RuntimeError(f"mpv exited with code {result.returncode}")
