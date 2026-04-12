"""YouTube search via yt-dlp — no API key required."""
from __future__ import annotations

import yt_dlp


def search_youtube(query: str, max_results: int = 15) -> tuple[list[dict], bool]:
    """Return up to *max_results* videos matching *query*.
    If *query* is a URL, it extracts that specific video or playlist.

    Returns: (results_list, is_playlist)
    """
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }
    
    # Logic to handle direct URLs or search queries
    source = query if query.startswith(("http://", "https://")) else f"ytsearch{max_results}:{query}"
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(source, download=False)
        except Exception:
            return [], False

    is_playlist = info.get("_type") == "playlist"
    
    if "entries" in info:
        entries = info["entries"]
    else:
        entries = [info]

    results: list[dict] = []
    for e in entries:
        if not e:
            continue
        # For flat extraction, id might be in 'id' or 'url'
        vid_id = e.get("id") or e.get("url", "").split("v=")[-1].split("&")[0] or "Unknown"
        results.append(
            {
                "id": vid_id,
                "title": e.get("title") or "Unknown",
                "channel": e.get("uploader") or e.get("channel") or "Unknown",
                "duration": e.get("duration"),
                "views": e.get("view_count"),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "thumbnail": e.get("thumbnail") or "",
            }
        )
    return results, is_playlist


