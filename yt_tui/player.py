import asyncio
import logging
import os
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)


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
    mpv_path = find_tool("mpv")
    if not mpv_path:
        raise RuntimeError("mpv not found")

    cmd = [mpv_path, "--really-quiet"]
    if ytdl_path:
        cmd.append(f"--script-opts=ytdl_hook-ytdl_path={ytdl_path}")
    
    cmd.append(url)
    
    if audio_only:
        cmd.append("--no-video")

    result = subprocess.run(cmd)
    return result.returncode


async def play_async(url: str, audio_only: bool = False, ytdl_path: str | None = None) -> int:
    """Spawn mpv asynchronously, returning the exit code when it finishes."""
    mpv_path = find_tool("mpv")
    if not mpv_path:
        raise RuntimeError("mpv not found")

    cmd = [mpv_path, "--really-quiet"]
    if ytdl_path:
        cmd.append(f"--script-opts=ytdl_hook-ytdl_path={ytdl_path}")

    cmd.append(url)

    if audio_only:
        cmd.append("--no-video")

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
        error_msg = f"mpv failed (returncode={proc.returncode}): {stderr.decode(errors='replace').strip()}"
        logger.error(error_msg)
        print(f"mpv command: {' '.join(cmd)}", file=sys.stderr)
        print(error_msg, file=sys.stderr)

    return proc.returncode
