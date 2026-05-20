#!/usr/bin/env bash
# YT-TUI setup — Unix/Linux/macOS
# Uses uv for all Python operations. Installs yt-tui globally.
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

# ── 2. Python ──────────────────────────────────────────────────
UV_PY=$(uv python find || command -v python3 || command -v python)
if [ -z "${UV_PY:-}" ]; then
  echo "!! No usable Python found — install Python 3.10+ and retry."
  exit 1
fi
echo ">> Python ${UV_PY}"

# ── 3. System deps ────────────────────────────────────────────
OS=""
case "$(uname -s)" in
  Linux*)   OS="linux";;
  Darwin*)  OS="macos";;
  *)        OS="unknown";;
esac

MISSING_SYSTEM=()
if ! command -v mpv >/dev/null 2>&1; then
  MISSING_SYSTEM+=("mpv")
fi
if ! command -v chafa >/dev/null 2>&1; then
  MISSING_SYSTEM+=("chafa")
fi

if [ ${#MISSING_SYSTEM[@]} -gt 0 ]; then
  echo ">> Missing system deps: ${MISSING_SYSTEM[*]} (thumbnails disabled without chafa)"
  case "$OS" in
    linux)
      if command -v dnf >/dev/null 2>&1; then
        echo "   Install with: sudo dnf install mpv chafa"
      elif command -v apt >/dev/null 2>&1; then
        echo "   Install with: sudo apt install mpv chafa"
      elif command -v pacman >/dev/null 2>&1; then
        echo "   Install with: sudo pacman -S mpv chafa"
      fi
      ;;
    macos)
      if command -v brew >/dev/null 2>&1; then
        echo "   Install with: brew install mpv chafa"
      else
        echo "   Install Homebrew first, then: brew install mpv chafa"
      fi
      ;;
  esac
fi

# ── 4. Global install ─────────────────────────────────────────
echo ">> Globally installing yt-tui…"
uv tool install -e . --python "$UV_PY"

# ── 5. Edge-cases: upgrade in-place if already present ────────
if command -v yt-tui >/dev/null 2>&1; then
  echo ">> yt-tui installed to $(command -v yt-tui)"
  yt-tui --version 2>/dev/null || true
else
  echo ">> yt-tui binary not in PATH — checking uv tools…"
  uv tool list 2>/dev/null
fi

echo ""
echo "=== Done ==="
echo "Run from anywhere:  yt-tui"
echo "Tests:              uv run -- pytest tests/ -v"
