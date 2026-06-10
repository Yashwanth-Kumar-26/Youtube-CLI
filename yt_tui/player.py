import asyncio
import logging
import os
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)

# ── Download quality ────────────────────────────────────────────
# Default: best video up to 1080p with best audio.
#
# Override via (in priority order):
#   1. YT_TUI_QUALITY          — full yt-dlp format string (advanced)
#   2. YT_TUI_VIDEO_HEIGHT     — video height cap  (e.g. 1080, 720, 2160)
#      + YT_TUI_AUDIO_BITRATE  — audio bitrate cap (e.g. 320, 256, 128)
#   3. hardcoded defaults below
#
# Audio-only mode (--no-video) only downloads audio — respects
# YT_TUI_AUDIO_BITRATE automatically.
#
# If the exact combination isn't available, yt-dlp auto-falls back
# to the next best stream.
DEFAULT_VIDEO_FORMAT = "bestvideo[height<=1080]+bestaudio/bestvideo+bestaudio/best"
DEFAULT_AUDIO_FORMAT = "bestaudio/best"


def _build_format(audio_only: bool = False) -> str:
    """Build yt-dlp format string from environment variables."""
    # 1. Full custom format — overrides everything
    custom = os.environ.get("YT_TUI_QUALITY")
    if custom:
        return custom

    # 2. Individual caps
    height = os.environ.get("YT_TUI_VIDEO_HEIGHT", "").strip()
    abr = os.environ.get("YT_TUI_AUDIO_BITRATE", "").strip()

    # Audio-only: just the best audio (with optional bitrate cap)
    if audio_only:
        if abr:
            return f"bestaudio[abr<={abr}]/bestaudio/best"
        return DEFAULT_AUDIO_FORMAT

    # Video mode: video + audio combo
    if not height and not abr:
        return DEFAULT_VIDEO_FORMAT

    video = f"bestvideo[height<={height}]" if height else "bestvideo"
    audio = f"bestaudio[abr<={abr}]" if abr else "bestaudio"
    return f"{video}+{audio}/bestvideo+bestaudio/best"


def _build_cmd(url: str, audio_only: bool = False, ytdl_path: str | None = None) -> list[str]:
    """Build the mpv command list with the resolved yt-dlp format."""
    mpv_path = find_tool("mpv")
    if not mpv_path:
        raise RuntimeError("mpv not found")

    fmt = _build_format(audio_only)
    logger.debug("yt-dlp format: %s — mpv command", fmt)

    cmd = [
        mpv_path, "--really-quiet",
        f"--ytdl-format={fmt}",
    ]
    if ytdl_path:
        cmd.append(f"--script-opts=ytdl_hook-ytdl_path={ytdl_path}")

    cmd.append(url)

    if audio_only:
        cmd.append("--no-video")

    return cmd


def find_tool(name: str) -> str | None:
    """Find an executable in PATH or common Windows locations."""
    if shutil.which(name):
        return name

    if sys.platform == "win32":
        # Search common Windows paths
        user_profile = os.environ.get("USERPROFILE", "")
        local_appdata = os.environ.get("LOCALAPPDATA", "")

        paths = [
            os.path.join(user_profile, "scoop", "shims"),
            os.path.join(local_appdata, "Microsoft", "WinGet", "Packages"),
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "mpv"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "mpv"),
        ]

        for p in paths:
            exe = os.path.join(p, f"{name}.exe")
            if os.path.exists(exe):
                return exe
    return None


def play(url: str, audio_only: bool = False, ytdl_path: str | None = None) -> int:
    """Spawn mpv for *url*, blocking until the user quits.
    Returns the exit code of mpv.
    """
    cmd = _build_cmd(url, audio_only, ytdl_path)
    logger.debug("mpv command: %s", " ".join(cmd))
    result = subprocess.run(cmd)
    return result.returncode


async def play_async(url: str, audio_only: bool = False, ytdl_path: str | None = None) -> int:
    """Spawn mpv asynchronously, returning the exit code when it finishes."""
    cmd = _build_cmd(url, audio_only, ytdl_path)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await proc.communicate()
    except asyncio.CancelledError:
        proc.kill()
        await proc.wait()
        raise

    if proc.returncode != 0:
        error_msg = f"mpv failed (returncode={proc.returncode}): {stderr.decode('utf-8', errors='replace').strip()}"
        logger.error(error_msg)
        print(f"mpv command: {' '.join(cmd)}", file=sys.stderr)
        print(error_msg, file=sys.stderr)

    return proc.returncode
