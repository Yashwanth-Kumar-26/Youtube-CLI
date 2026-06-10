"""YouTube search via yt-dlp — no API key required."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yt_dlp


@dataclass
class SearchResult:
    """A single video or playlist entry from YouTube search.

    All callers should use these typed fields rather than raw dict keys.
    """
    id: str
    title: str
    channel: str
    duration: int | None = None
    views: int | None = None
    url: str = ""
    thumbnail: str = ""
    # Arbitrary extra metadata from yt-dlp (future-proofing)
    extra: dict[str, Any] = field(default_factory=dict)


def search_youtube(query: str, max_results: int = 50) -> tuple[list[SearchResult], bool]:
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

        if not info:
            return [], False

        is_playlist = info.get("_type") == "playlist"

    if "entries" in info:
        entries = info["entries"]
    else:
        entries = [info]

    results: list[SearchResult] = []
    for e in entries:
        if not e:
            continue
        # For flat extraction, id might be in 'id' or 'url'
        vid_id = e.get("id") or e.get("url", "").split("v=")[-1].split("&")[0] or "Unknown"

        # yt-dlp returns thumbnails as a list; use highest resolution
        thumb = e.get("thumbnail")
        if not thumb:
            thumbs = e.get("thumbnails") or []
            thumb = thumbs[-1].get("url", "") if thumbs else ""

        results.append(
            SearchResult(
                id=vid_id,
                title=e.get("title") or "Unknown",
                channel=e.get("uploader") or e.get("channel") or "Unknown",
                duration=e.get("duration"),
                views=e.get("view_count"),
                url=f"https://www.youtube.com/watch?v={vid_id}",
                thumbnail=thumb,
                extra={k: v for k, v in e.items() if k not in (
                    "id", "title", "uploader", "channel", "duration",
                    "view_count", "url", "thumbnail", "thumbnails",
                )},
            )
        )
    return results, is_playlist


