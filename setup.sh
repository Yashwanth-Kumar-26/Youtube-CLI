#!/usr/bin/env bash
# YT-TUI setup — Unix/Linux/macOS
# Installs system deps + uses uv to install yt-tui globally.
#
# Override download quality by setting YT_TUI_QUALITY before running:
#   export YT_TUI_QUALITY="bestvideo[height<=720]+bestaudio/best[height<=720]"
#   ./setup.sh
#
# Default quality: bestvideo[height<=1080]+bestaudio/best[height<=1080]
set -eufo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== YT-TUI Setup ==="

# ── 1. uv ──────────────────────────────────────────────────────
if ! command -v uv >/dev/null 2>&1; then
  echo ">> uv not found — installing…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
echo ">> uv $(uv --version)"

# ── 2. Python 3.10+ ──────────────────────────────────────────────
PYTHON_EXE=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    full_ver=$("$candidate" --version 2>&1)
    ver=$(echo "$full_ver" | grep -oP '\d+\.\d+')
    major="${ver%.*}"
    minor="${ver#*.}"
    if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; }; then
      PYTHON_EXE=$(command -v "$candidate")
      echo ">> Python $(basename "$PYTHON_EXE") $("$PYTHON_EXE" --version 2>&1 | grep -oP 'Python \S+')"
      break
    fi
  fi
done

if [ -z "$PYTHON_EXE" ]; then
  echo ">> Python 3.10+ not found — checking uv-managed interpreters…"
  PYTHON_EXE=$(uv python find 3.10 2>/dev/null || true)
fi

if [ -z "$PYTHON_EXE" ]; then
  echo ">> Installing Python 3.10 via uv…"
  uv python install 3.10
  PYTHON_EXE=$(uv python find 3.10 2>/dev/null || true)
fi

if [ -z "$PYTHON_EXE" ]; then
  echo "!! Python 3.10+ required — install it and re-run setup."
  exit 1
fi

echo ">> Python $(basename "$PYTHON_EXE") $("$PYTHON_EXE" --version 2>&1 | grep -oP 'Python \S+')"

# ── 3. System dependencies ─────────────────────────────────────
OS=""
PKG_MGR=""
INSTALL_CMD=""

case "$(uname -s)" in
  Linux*)
    OS="linux"
    if   command -v dnf    >/dev/null 2>&1; then PKG_MGR="dnf";    INSTALL_CMD="sudo dnf install -y"
    elif command -v apt    >/dev/null 2>&1; then PKG_MGR="apt";    INSTALL_CMD="sudo apt install -y"
    elif command -v pacman >/dev/null 2>&1; then PKG_MGR="pacman"; INSTALL_CMD="sudo pacman -S --noconfirm"
    elif command -v zypper >/dev/null 2>&1; then PKG_MGR="zypper"; INSTALL_CMD="sudo zypper install -y"
    fi
    ;;
  Darwin*)
    OS="macos"
    if command -v brew >/dev/null 2>&1; then
      PKG_MGR="brew"
      INSTALL_CMD="brew install"
    fi
    ;;
  *)
    OS="unknown"
    ;;
esac

MISSING=()
command -v mpv   >/dev/null 2>&1 || MISSING+=("mpv")
command -v chafa >/dev/null 2>&1 || MISSING+=("chafa")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo ">> Installing missing system packages: ${MISSING[*]}"
  if [ -n "$INSTALL_CMD" ]; then
    $INSTALL_CMD "${MISSING[@]}"
  else
    echo "!! No supported package manager found."
    echo "   Please install manually: ${MISSING[*]}"
    case "$OS" in
      linux)
        echo "   Try: sudo dnf install ${MISSING[*]}"
        echo "   Or:  sudo apt install ${MISSING[*]}"
        echo "   Or:  sudo pacman -S ${MISSING[*]}"
        echo "   Or:  sudo zypper install ${MISSING[*]}"
        ;;
      macos)
        echo "   Install Homebrew first, then: brew install ${MISSING[*]}"
        ;;
    esac
  fi
fi

# ── 4. Global install ─────────────────────────────────────────
echo ">> Globally installing yt-tui…"
uv tool install . --python "$PYTHON_EXE"

# ── 5. Final check ────────────────────────────────────────────
if command -v yt-tui >/dev/null 2>&1; then
  echo ">> yt-tui installed to $(command -v yt-tui)"
else
  echo ">> yt-tui binary not in PATH — checking uv tools…"
  uv tool list 2>/dev/null
fi

# ── 6. Download quality config ──────────────────────────────
_detect_profile() {
  if [ -n "${ZSH_VERSION-}" ]; then
    echo "$HOME/.zshrc"
  elif [ -n "${BASH_VERSION-}" ]; then
    case "$(uname -s)" in
      Darwin*) echo "$HOME/.bash_profile" ;;
      *)       echo "$HOME/.bashrc" ;;
    esac
  else
    echo "$HOME/.profile"
  fi
}

echo ""
echo "── Download Quality ────────────────────────────────────"

# Video quality menu
echo "Select VIDEO quality (press Enter for default 1080p):"
echo "  1) 4K     (2160p) — best available up to 4K"
echo "  2) 1440p          — best available up to 1440p"
echo "  3) 1080p          — best available up to 1080p  (default)"
echo "  4) 720p           — best available up to 720p"
echo "  5) 480p           — best available up to 480p"
echo "  6) 360p           — best available up to 360p"
echo "  7) Best  (no cap) — highest available"
echo "  q) Skip           — keep 1080p default"
echo ""
read -r -p "Video choice [3/q]: " video_choice

height=""
case "${video_choice:-3}" in
  1) height="2160" ;;
  2) height="1440" ;;
  3|"") height="1080" ;;
  4) height="720" ;;
  5) height="480" ;;
  6) height="360" ;;
  7) height="" ;;   # Best — no cap
  *) height="1080" ;;  # default
esac

# Audio quality menu
echo ""
echo "Select AUDIO quality (press Enter for default Best):"
echo "  1) 320 kbps  — best audio up to 320kbps"
echo "  2) 256 kbps  — best audio up to 256kbps"
echo "  3) 192 kbps  — best audio up to 192kbps"
echo "  4) 128 kbps  — best audio up to 128kbps"
echo "  5) Best      — highest available  (default)"
echo "  q) Skip      — keep default"
echo ""
read -r -p "Audio choice [5/q]: " audio_choice

abr=""
case "${audio_choice:-5}" in
  1) abr="320" ;;
  2) abr="256" ;;
  3) abr="192" ;;
  4) abr="128" ;;
  5|"") abr="" ;;   # Best — no cap
  *) abr="" ;;       # default
esac

# Build the format string from height/abr choices
if [ -n "$height" ] && [ -n "$abr" ]; then
  quality_val="bestvideo[height<=${height}]+bestaudio[abr<=${abr}]/bestvideo+bestaudio/best"
elif [ -n "$height" ]; then
  quality_val="bestvideo[height<=${height}]+bestaudio/bestvideo+bestaudio/best"
elif [ -n "$abr" ]; then
  quality_val="bestvideo+bestaudio[abr<=${abr}]/bestvideo+bestaudio/best"
else
  quality_val=""  # neither set — use player.py default
fi

# Persist to shell profile
profile_file="$(_detect_profile)"

if [ -n "$quality_val" ]; then
  line="export YT_TUI_QUALITY=\"$quality_val\""
  if grep -qs "export YT_TUI_QUALITY=" "$profile_file" 2>/dev/null; then
    # Cross-platform sed in-place (BSD sed on macOS needs .bak arg)
    sed -i.bak "s|^export YT_TUI_QUALITY=.*|$line|" "$profile_file" && rm -f "$profile_file.bak"
    echo ""
    echo ">> Updated YT_TUI_QUALITY in $profile_file"
  else
    printf '\n# YT-TUI download quality\n' >> "$profile_file"
    echo "$line" >> "$profile_file"
    echo ""
    echo ">> Added YT_TUI_QUALITY to $profile_file"
  fi
  echo "   Video:  ${height:-best (no cap)}p"
  echo "   Audio:  ${abr:-best (no cap)} kbps"
  echo "   String: $quality_val"
  echo "   (restart your shell or 'source $profile_file' to apply)"
else
  echo ""
  echo ">> Using default quality (no profile change)"
  echo "   Default: 1080p video + best audio"
fi

echo ""
echo "=== Done ==="
echo "Run from anywhere:  yt-tui"
echo "Incognito mode:     yt-tui incog"
echo "Change quality:     edit YT_TUI_QUALITY in $profile_file"
echo "Tests:              uv run -- pytest tests/ -v"
