"""Tests for search.py"""
from unittest.mock import MagicMock, patch

import pytest

from yt_tui.search import SearchResult, search_youtube


FAKE_ENTRIES = [
    {
        "id": "abc123",
        "title": "Linux Tips",
        "uploader": "TechChannel",
        "duration": 300,
        "view_count": 50000,
        "thumbnail": "https://img.youtube.com/vi/abc123/0.jpg",
    },
    {
        "id": "def456",
        "title": "Terminal Tricks",
        "channel": "DevChannel",
        "duration": None,
        "view_count": None,
        "thumbnail": "",
    },
    {
        "id": "ghi789",
        "title": "Flat Extract",
        "uploader": "FlatChan",
        "duration": 120,
        "view_count": 1000,
        # Simulate flat extraction: thumbnail key missing, thumbnails list present
        "thumbnails": [{"url": "https://i.ytimg.com/vi/ghi789/hq720.jpg"}],
    },
]


def _mock_ydl(entries):
    ydl = MagicMock()
    ydl.__enter__ = lambda s: s
    ydl.__exit__ = MagicMock(return_value=False)
    ydl.extract_info.return_value = {"entries": entries}
    return ydl


@patch("yt_tui.search.yt_dlp.YoutubeDL")
def test_search_returns_results(mock_cls):
    mock_cls.return_value = _mock_ydl(FAKE_ENTRIES)
    results, is_playlist = search_youtube("linux tips", max_results=5)
    assert len(results) == 3
    assert isinstance(results[0], SearchResult)
    assert results[0].id == "abc123"
    assert results[0].title == "Linux Tips"
    assert results[0].url == "https://www.youtube.com/watch?v=abc123"
    assert results[1].channel == "DevChannel"
    assert is_playlist is False


@patch("yt_tui.search.yt_dlp.YoutubeDL")
def test_search_thumbnail_from_list(mock_cls):
    """Thumbnail should fall back to thumbnails[-1] (highest res) when thumbnail key is missing."""
    mock_cls.return_value = _mock_ydl(FAKE_ENTRIES)
    results, _ = search_youtube("test", max_results=5)
    # Entry 0 has direct thumbnail
    assert results[0].thumbnail == "https://img.youtube.com/vi/abc123/0.jpg"
    # Entry 2 uses thumbnails list fallback
    assert results[2].thumbnail == "https://i.ytimg.com/vi/ghi789/hq720.jpg"
    # Entry 1 has empty thumbnail
    assert results[1].thumbnail == ""


@patch("yt_tui.search.yt_dlp.YoutubeDL")
def test_search_skips_none_entries(mock_cls):
    mock_cls.return_value = _mock_ydl([None, FAKE_ENTRIES[0]])
    results, is_playlist = search_youtube("test")
    assert len(results) == 1
    assert results[0].id == "abc123"
    assert is_playlist is False


@patch("yt_tui.search.yt_dlp.YoutubeDL")
def test_search_empty(mock_cls):
    mock_cls.return_value = _mock_ydl([])
    results, is_playlist = search_youtube("nothing")
    assert results == []
    assert is_playlist is False


@patch("yt_tui.search.yt_dlp.YoutubeDL")
def test_search_none_info(mock_cls):
    ydl = _mock_ydl([])
    ydl.extract_info.return_value = None
    mock_cls.return_value = ydl
    results, is_playlist = search_youtube("test")
    assert results == []
    assert is_playlist is False

