# YT-CLI

A lightweight, terminal-native YouTube client. Search, preview, and stream videos without leaving your shell.

## Requirements

- Python 3.10+
- [mpv](https://mpv.io/) — video playback
- [chafa](https://hpjansson.org/chafa/) — thumbnail rendering *(optional)*

Install system deps:

```bash
# Fedora
sudo dnf install mpv chafa

# Ubuntu / Debian
sudo apt install mpv chafa

# Arch
sudo pacman -S mpv chafa
```

## Install

```bash
git clone https://github.com/you/yt-cli
cd yt-cli
pip install -e .
```

## Usage

```bash
yt-cli
```

The TUI launches with the search bar focused. Start typing and press **Enter**.

## Keyboard Reference

| Key | Action |
|-----|--------|
| `/` | Focus search bar |
| `↑ / ↓` | Navigate results |
| `Enter` | Play selected video |
| `?` | Help screen |
| `q` | Quit |

**During mpv playback:**

| Key | Action |
|-----|--------|
| `Space` | Pause / resume |
| `← / →` | Seek |
| `↑ / ↓` | Volume |
| `q` | Return to YT-CLI |

## Project Structure

```
yt-cli/
├── main.py        # Entry point
├── search.py      # yt-dlp search wrapper
├── player.py      # mpv subprocess
├── thumbnail.py   # chafa thumbnail render
├── ui.py          # Textual TUI
├── utils.py       # Formatting + JSON helpers
├── tests/
│   ├── test_search.py
│   ├── test_player.py
│   └── test_utils.py
└── pyproject.toml
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Notes

- Uses `yt-dlp` for YouTube access — no API key needed.
- All user data stored in `~/.yt-cli/` as flat JSON (Phase 2).
- Thumbnails require a terminal with Unicode/sixel support; silently skipped otherwise.
=======
