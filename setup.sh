#!/usr/bin/env bash
# YT-TUI setup — Unix/Linux/macOS
# Uses uv for all Python operations.

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
UV_PY=$(uv python find 3.10||true)
if [ -z "${UV_PY:-}" ]; then
  echo "!! Python 3.10+ required — install it and retry."
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

# ── 4. venv + install ─────────────────────────────────────────
echo ">> Creating virtual environment…"
uv venv
echo ">> Installing yt-tui (editable)…"
uv pip install --python "$UV_PY" -e .

echo ""
echo "=== Done ==="
if [ -f ".venv/bin/activate" ]; then
  echo "Activate:   source .venv/bin/activate"
else
  echo "Activate:   uv run -- python -m yt_tui"
fi
echo "Run:        yt-tui"
echo "Tests:      uv run -- pytest tests/ -v"
