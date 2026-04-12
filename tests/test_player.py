"""Tests for player.py"""
import subprocess
from unittest.mock import patch

import pytest

from player import play


@patch("player.shutil.which", return_value="/usr/bin/mpv")
@patch("player.subprocess.run")
def test_play_calls_mpv(mock_run, mock_which):
    mock_run.return_value = subprocess.CompletedProcess([], 0)
    play("https://www.youtube.com/watch?v=abc123")
    cmd = mock_run.call_args[0][0]
    assert "mpv" in cmd
    assert "https://www.youtube.com/watch?v=abc123" in cmd


@patch("player.shutil.which", return_value="/usr/bin/mpv")
@patch("player.subprocess.run")
def test_play_audio_only(mock_run, mock_which):
    mock_run.return_value = subprocess.CompletedProcess([], 0)
    play("https://www.youtube.com/watch?v=abc123", audio_only=True)
    cmd = mock_run.call_args[0][0]
    assert "--no-video" in cmd


@patch("player.shutil.which", return_value="/usr/bin/mpv")
@patch("player.subprocess.run")
def test_play_user_quit_no_error(mock_run, mock_which):
    mock_run.return_value = subprocess.CompletedProcess([], 4)
    play("https://www.youtube.com/watch?v=abc123")  # should not raise


@patch("player.shutil.which", return_value="/usr/bin/mpv")
@patch("player.subprocess.run")
def test_play_bad_exit_raises(mock_run, mock_which):
    mock_run.return_value = subprocess.CompletedProcess([], 1)
    with pytest.raises(RuntimeError):
        play("https://www.youtube.com/watch?v=abc123")


@patch("player.shutil.which", return_value=None)
def test_play_no_mpv_exits(mock_which):
    with pytest.raises(SystemExit):
        play("https://www.youtube.com/watch?v=abc123")
