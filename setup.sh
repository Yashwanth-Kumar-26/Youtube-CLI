#!/usr/bin/env bash
# YT-TUI setup — Unix/Linux/macOS
# Installs system deps + uses uv to install yt-tui globally.
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

echo ""
echo "=== Done ==="
echo "Run from anywhere:  yt-tui"
echo "Incognito mode:     yt-tui incog"
echo "Tests:              uv run -- pytest tests/ -v"
