"""Tests for search.py"""
from unittest.mock import MagicMock, patch

import pytest

from search import search_youtube


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
]


def _mock_ydl(entries):
    ydl = MagicMock()
    ydl.__enter__ = lambda s: s
    ydl.__exit__ = MagicMock(return_value=False)
    ydl.extract_info.return_value = {"entries": entries}
    return ydl


@patch("search.yt_dlp.YoutubeDL")
def test_search_returns_results(mock_cls):
    mock_cls.return_value = _mock_ydl(FAKE_ENTRIES)
    results = search_youtube("linux tips", max_results=2)
    assert len(results) == 2
    assert results[0]["id"] == "abc123"
    assert results[0]["title"] == "Linux Tips"
    assert results[0]["url"] == "https://www.youtube.com/watch?v=abc123"
    assert results[1]["channel"] == "DevChannel"


@patch("search.yt_dlp.YoutubeDL")
def test_search_skips_none_entries(mock_cls):
    mock_cls.return_value = _mock_ydl([None, FAKE_ENTRIES[0]])
    results = search_youtube("test")
    assert len(results) == 1


@patch("search.yt_dlp.YoutubeDL")
def test_search_empty(mock_cls):
    mock_cls.return_value = _mock_ydl([])
    assert search_youtube("nothing") == []


@patch("search.yt_dlp.YoutubeDL")
def test_search_none_info(mock_cls):
    ydl = _mock_ydl([])
    ydl.extract_info.return_value = None
    mock_cls.return_value = ydl
    assert search_youtube("test") == []
