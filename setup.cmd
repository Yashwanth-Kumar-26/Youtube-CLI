@echo off
:: YT-TUI setup — Windows
:: Uses uv for all Python operations.

echo === YT-TUI Setup ===

:: 1. uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing uv…
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1|iex"
    call %LOCALAPPDATA%\uv\uv-setup\activate.bat
)
uv --version

:: 2. System deps
where mpv >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARN] mpv not found — install from https://mpv.io/installation/
    echo        Thumbnails will also be disabled without chafa.
)
where chafa >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARN] chafa not found — fetch via Scoop: scoop install chafa
    echo        Thumbnails disabled.
)

:: 3. venv + install
echo.
echo Creating virtual environment…
uv venv
echo Installing yt-tui (editable)…
uv pip install -e .

echo.
echo === Done ===
echo Activate:  .venv\Scripts\activate
echo Run:       yt-tui
echo Tests:     uv run -- pytest tests/ -v
