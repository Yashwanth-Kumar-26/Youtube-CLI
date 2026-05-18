<p align="center">
  <img src="yt_tui/yt-tui.png" alt="YT-TUI Logo" width="512" />
</p>

<h1 align="center">YT-TUI</h1>

<p align="center">
  <strong>A lightweight, terminal-native YouTube client</strong><br/>
  Search, preview, and stream videos — no API key required, no browser needed.
</p>

<p align="center">
  <a href="https://github.com/Yashwanth-Kumar-26/Youtube-TUI"><img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" /></a>
  <a href="https://github.com/Yashwanth-Kumar-26/Youtube-TUI"><img src="https://img.shields.io/badge/Textual-TUI-green?logo=terminal" /></a>
  <a href="https://github.com/Yashwanth-Kumar-26/Youtube-TUI"><img src="https://img.shields.io/badge/License-MIT-yellow?logo=law" /></a>
</p>

---

## Features

- **Universal Search** — keywords or direct YouTube video/playlist URLs
- **Side Navigation** — switch between Search and History views
- **Persistent History** — searches and watch history saved across sessions
- **Playlist Support** — auto-extract and list all videos from playlist links
- **Playback Options** — Video or Audio-only mode per session
- **Autoplay** — auto-advance through playlist tracks
- **Asynchronous Thumbnails** — high-performance ANSI-art previews, non-blocking

## Requirements

- Python 3.10+
- [mpv](https://mpv.io/) — video playback
- [chafa](https://hpjansson.org/chafa/) — thumbnail rendering

### System Dependencies

```bash
# Fedora
sudo dnf install mpv chafa

# Ubuntu / Debian
sudo apt install mpv chafa

# Arch
sudo pacman -S mpv chafa

# macOS (Homebrew)
brew install mpv chafa

# Windows (Scoop)
scoop install mpv chafa

# Windows (Winget)
winget install shinchiro.mpv Chafa
```

## Installation

```bash
git clone https://github.com/Yashwanth-Kumar-26/Youtube-TUI.git
cd Youtube-TUI
pip install -e .
```

## Usage

```bash
yt-tui
```

The TUI launches with the search bar focused. Type or paste a URL and press **Enter**.

## Keyboard Reference

| Key | Action |
|-----|--------|
| `F1` | Help screen |
| `/` | Focus search bar |
| `s` | Switch to Search tab |
| `h` | Switch to History tab |
| `a` | Toggle Autoplay (ON/OFF) |
| `↑ / ↓` | Navigate results |
| `Enter` | Choose mode and play selected video |
| `Ctrl+Q` | Quit |

**During mpv playback:**

| Key | Action |
|-----|--------|
| `Space` | Pause / resume |
| `← / →` | Seek backward / forward |
| `↑ / ↓` | Volume up / down |
| `q` | Stop and return to YT-TUI |

## Project Structure

```
yt-tui/
├── yt_tui/        # Package directory
│   ├── __init__.py   # Package init, exports main()
│   ├── cli.py        # Entry point logic
│   ├── search.py     # yt-dlp search and playlist wrapper
│   ├── player.py     # mpv subprocess handler
│   ├── thumbnail.py  # chafa thumbnail rendering engine
│   ├── ui.py         # Textual TUI and state management
│   └── utils.py      # Formatting and I/O helpers
├── tests/         # Unit tests
├── yt-tui.png     # Project logo
└── pyproject.toml # Project metadata and dependencies
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Notes

- Uses `yt-dlp` for YouTube access — **no API key needed**
- All user data stored in `~/.yt-tui/` as flat JSON
- **Cross-Platform**: developed on Linux — Windows and macOS support experimental
- **Thumbnails**: require a terminal with Unicode/ANSI support (Windows Terminal, iTerm2, modern Linux term). Silently skipped if tools missing
- **Audio Mode**: mpv runs with `--no-video` flag to save bandwidth
