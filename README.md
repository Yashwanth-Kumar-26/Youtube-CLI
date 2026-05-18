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
- [mpv](https://mpv.io/) — Video & Audio playback
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

Run `setup.sh` (Unix/Linux/macOS) or `setup.cmd` (Windows). Uses `uv` under the hood — installs `yt-tui` globally so it works from any directory.

### Unix/Linux/macOS
```bash
git clone https://github.com/Yashwanth-Kumar-26/Youtube-TUI.git
cd Youtube-TUI
chmod +x setup.sh 
./setup.sh
```

### Windows
```cmd
git clone https://github.com/Yashwanth-Kumar-26/Youtube-TUI.git
cd Youtube-TUI
setup.cmd           
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


## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Acknowledgement

YT-TUI is built on top of the incredible [yt-dlp](https://github.com/yt-dlp/yt-dlp) project. Massive thanks to the yt-dlp maintainers and community for keeping YouTube accessible and open.

## Notes

- Uses `yt-dlp` for YouTube access — **no API key needed**
- All user data stored in `~/.yt-tui/` as flat JSON
- **Cross-Platform**: developed on Linux — Windows and macOS support experimental
- **Thumbnails**: require a terminal with Unicode/ANSI support (Windows Terminal, iTerm2, modern Linux term). Silently skipped if tools missing
- **Audio Mode**: mpv runs with `--no-video` flag to save bandwidth
