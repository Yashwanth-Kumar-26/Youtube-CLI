"""Tests for utils.py"""
import json
from pathlib import Path

import pytest

from yt_tui.utils import fmt_duration, fmt_views, load_json, save_json


@pytest.mark.parametrize("secs,expected", [
    (None, "--:--"),
    (0, "0:00"),
    (59, "0:59"),
    (60, "1:00"),
    (3661, "1:01:01"),
])
def test_fmt_duration(secs, expected):
    assert fmt_duration(secs) == expected


@pytest.mark.parametrize("count,expected", [
    (None, "N/A"),
    (999, "999"),
    (1_000, "1.0K"),
    (1_500, "1.5K"),
    (1_000_000, "1.0M"),
    (2_500_000, "2.5M"),
])
def test_fmt_views(count, expected):
    assert fmt_views(count) == expected


def test_load_json_missing(tmp_path):
    assert load_json(tmp_path / "nope.json") == []


def test_load_json_invalid(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    assert load_json(p) == []


def test_save_and_load_json(tmp_path, monkeypatch):
    from yt_tui.utils import DATA_DIR
    monkeypatch.setattr("yt_tui.utils.DATA_DIR", tmp_path)
    p = tmp_path / "test.json"
    data = [{"id": "abc", "title": "Test"}]
    save_json(p, data)
    assert load_json(p) == data


def test_history_manager(tmp_path, monkeypatch):
    from yt_tui.utils import HistoryManager
    monkeypatch.setattr("yt_tui.utils.DATA_DIR", tmp_path)
    
    # Test search history
    HistoryManager.add_search("python tutorial")
    HistoryManager.add_search("textual tui")
    history = HistoryManager.get_search_history()
    assert len(history) == 2
    assert history[0]["query"] == "textual tui"
    
    # Test duplicate search (moves to top)
    HistoryManager.add_search("python tutorial")
    history = HistoryManager.get_search_history()
    assert len(history) == 2
    assert history[0]["query"] == "python tutorial"
    
    # Test watch history
    video = {"id": "123", "title": "Great Video"}
    HistoryManager.add_watch(video)
    watch_history = HistoryManager.get_watch_history()
    assert len(watch_history) == 1
    assert watch_history[0]["id"] == "123"
