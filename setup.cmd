@echo off
:: YT-TUI setup — Windows
:: Uses uv for all Python operations. Installs yt-tui globally.

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
    echo        Thumbnails disabled without chafa.
)
where chafa >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARN] chafa not found — fetch via Scoop: scoop install chafa
    echo        Thumbnails disabled.
)

:: 3. Python 3.10+
echo.
echo Resolving Python 3.10+ interpreter…
for /f "usebackq delims=" %%I in (`uv python find 3.10 2^>nul`) do set "PYTHON_EXE=%%I"
if not defined PYTHON_EXE (
    echo [ERROR] Python 3.10+ not found.
    echo         Install Python 3.10+ or run: uv python install 3.10
    exit /b 1
)
echo ^> Python %PYTHON_EXE%

:: 4. Global install
echo.
echo Globally installing yt-tui…
uv tool install -e .

echo.
echo === Done ===
echo Run from anywhere:  yt-tui
