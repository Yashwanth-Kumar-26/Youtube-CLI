# YT-CLI

A lightweight, terminal-native YouTube client. Search, preview, and stream videos without leaving your shell. No API key required.

## Features

- **Universal Search**: Type keywords or paste direct YouTube video and playlist URLs.
- **Playlist Support**: Automatically extracts and lists all videos from pasted playlist links.
- **Playback Options**: Choose between Video and Audio-only mode for every session.
- **Autoplay**: Automatically advances to the next video in the list (especially for playlists).
- **Asynchronous Thumbnails**: High-performance ANSI-art previews that don't block the UI.

## Requirements

- Python 3.10+
- [mpv](https://mpv.io/) — video playback
- [chafa](https://hpjansson.org/chafa/) — thumbnail rendering (optional)

### System Dependencies

```bash
# Fedora
sudo dnf install mpv chafa

# Ubuntu / Debian
sudo apt install mpv chafa

# Arch
sudo pacman -S mpv chafa

# macOS (Homebrew - Under Development)
brew install mpv chafa

# Windows (Scoop - Under Development)
scoop install mpv chafa

# Windows (Winget - Under Development)
winget install shinchiro.mpv Chafa

```

## Installation

```bash
git clone https://github.com/Yashwanth-Kumar-26/Youtube-CLI.git
cd Youtube-CLI
pip install -e .
```

## Usage

```bash
yt-cli
```

The TUI launches with the search bar focused. Start typing or paste a URL and press **Enter**.

## Keyboard Reference

| Key | Action |
|-----|--------|
| `/` | Focus search bar |
| `a` | Toggle Autoplay (ON/OFF) |
| `↑ / ↓` | Navigate results |
| `Enter` | Choose mode and play selected video |
| `?` | Help screen |
| `q` | Quit |

**During mpv playback:**

| Key | Action |
|-----|--------|
| `Space` | Pause / resume |
| `← / →` | Seek backward / forward |
| `↑ / ↓` | Volume up / down |
| `q` | Stop and return to YT-CLI |

## Project Structure

```
yt-cli/
├── main.py        # Entry point
├── search.py      # yt-dlp search and playlist wrapper
├── player.py      # mpv subprocess handler
├── thumbnail.py   # chafa thumbnail rendering engine
├── ui.py          # Textual TUI and state management
├── utils.py       # Formatting and I/O helpers
├── tests/         # Unit tests
└── pyproject.toml # Project metadata and dependencies
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Notes

- Uses `yt-dlp` for YouTube access — no API key needed.
- All user data stored in `~/.yt-cli/` as flat JSON.
- **Cross-Platform**: Developed on Linux. **Windows and macOS support are currently under development (Experimental)**.
- **Thumbnails**: Require a terminal with Unicode/ANSI support (like Windows Terminal, iTerm2, or any modern Linux terminal). Silently skipped if tools are missing.
- **Audio Mode**: In Audio mode, `mpv` runs with the `--no-video` flag to save bandwidth.

