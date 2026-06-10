import asyncio
import logging
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Portable mpv download ──────────────────────────────────────
# URLs for portable mpv builds (used when system mpv is not found).
# These are downloaded and cached on first run — no installer popups.
MPV_DOWNLOAD_URLS: dict[str, dict[str, str]] = {
    "linux": {
        "x86_64": (
            "https://github.com/leon-richardt/mpv-static-builds/releases/"
            "download/0.39.0/mpv-0.39.0-linux-x86_64.tar.gz"
        ),
        "aarch64": (
            "https://github.com/leon-richardt/mpv-static-builds/releases/"
            "download/0.39.0/mpv-0.39.0-linux-aarch64.tar.gz"
        ),
    },
    "darwin": {
        "x86_64": (
            "https://github.com/leon-richardt/mpv-static-builds/releases/"
            "download/0.39.0/mpv-0.39.0-darwin-x86_64.tar.gz"
        ),
        "arm64": (
            "https://github.com/leon-richardt/mpv-static-builds/releases/"
            "download/0.39.0/mpv-0.39.0-darwin-arm64.tar.gz"
        ),
    },
    "windows": {
        "x86_64": (
            "https://sourceforge.net/projects/mpv-player-windows/"
            "files/64bit/mpv-0.39.0-x86_64.7z/download"
        ),
    },
}


def _get_cache_dir() -> Path:
    """Platform-appropriate cache directory for yt-tui."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path.home() / ".cache"
    return base / "yt-tui"


def _arch() -> str:
    """Normalize architecture name for download URL lookup."""
    raw = platform.machine().lower()
    mapping = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "aarch64",
        "i386": "x86_64",
        "i686": "x86_64",
    }
    return mapping.get(raw, "x86_64")


def _download_mpv(target: Path) -> None:
    """Download portable mpv to *target* path — no installer, no popups."""
    system = platform.system().lower()
    arch = _arch()

    url = MPV_DOWNLOAD_URLS.get(system, {}).get(arch)
    if not url:
        raise RuntimeError(
            f"No pre-built mpv available for {system}/{arch}. "
            f"Install mpv manually: https://mpv.io/installation/"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    archive_path = target.parent / "mpv_download.tmp"

    try:
        logger.info("Downloading mpv (%s/%s) …", system, arch)
        urllib.request.urlretrieve(url, archive_path)

        if system == "windows":
            _extract_windows(archive_path, target)
        else:
            _extract_tar(archive_path, target)

        target.chmod(0o755)
        logger.info("mpv cached at %s", target)

    except Exception as exc:
        raise RuntimeError(
            f"Failed to download mpv: {exc}\n"
            f"Install manually: https://mpv.io/installation/"
        ) from exc
    finally:
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)


def _extract_windows(archive: Path, target: Path) -> None:
    """Extract .7z archive using py7zr (pure Python, no system deps)."""
    import py7zr  # noqa: PLC0415 — pure Python, always available
    with py7zr.SevenZipFile(archive, mode="r") as zf:
        zf.extractall(path=target.parent)


def _extract_tar(archive: Path, target: Path) -> None:
    """Extract .tar.gz archive and move mpv binary to *target*."""
    # macOS/Linux tarballs contain a single top-level dir with the binary inside
    extracted_dir = target.parent / "_extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=extracted_dir)

    # Find the mpv binary (nested one level deep)
    for item in extracted_dir.rglob("mpv"):
        if item.is_file() and item.parent != extracted_dir:
            shutil.move(str(item), str(target))
            break

    # Cleanup
    shutil.rmtree(extracted_dir, ignore_errors=True)
    if not target.exists():
        raise RuntimeError("Could not locate mpv binary in the downloaded archive.")


def _ensure_mpv() -> str:
    """Return path to mpv — checking cache, then auto-downloading if needed."""
    cache = _get_cache_dir()
    binary = "mpv.exe" if sys.platform == "win32" else "mpv"
    mpv_path = cache / binary
    if mpv_path.exists():
        return str(mpv_path)
    _download_mpv(mpv_path)
    return str(mpv_path)


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
    """Find an executable in PATH, common Windows locations, or auto-download mpv."""
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
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), name),
        ]

        for p in paths:
            exe = os.path.join(p, f"{name}.exe")
            if os.path.exists(exe):
                return exe

    # ── Auto-download mpv as a last resort ──
    if name == "mpv":
        try:
            logger.info("mpv not found on system — downloading portable build …")
            return _ensure_mpv()
        except Exception as exc:
            logger.warning("Could not auto-download mpv: %s", exc)

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
