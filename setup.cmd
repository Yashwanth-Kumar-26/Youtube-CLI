@echo off
:: YT-TUI setup — Windows
:: Installs system deps via winget + uses uv to install yt-tui globally.
::
:: Override download quality by setting YT_TUI_QUALITY before running:
::   set YT_TUI_QUALITY=bestvideo[height<=720]+bestaudio/best[height<=720]
::   setup.cmd
::
:: Default quality: bestvideo[height<=1080]+bestaudio/best[height<=1080]
setlocal enabledelayedexpansion

echo === YT-TUI Setup ===

:: ── 1. uv ──────────────────────────────────────────────────────
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing uv…
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1|iex"
    call %LOCALAPPDATA%\uv\uv-setup\activate.bat
)
uv --version

:: ── 2. System dependencies ─────────────────────────────────────
set "MISSING="
where mpv >nul 2>nul
if %errorlevel% neq 0 set "MISSING=%MISSING% mpv"
where chafa >nul 2>nul
if %errorlevel% neq 0 set "MISSING=%MISSING% chafa"

if defined MISSING (
    echo.
    echo Installing missing system packages:%MISSING%
    echo Requests admin privileges for installation…
    
    where winget >nul 2>nul
    if !errorlevel! equ 0 (
        for %%p in (%MISSING%) do (
            echo Installing %%p…
            winget install %%p --accept-package-agreements --accept-source-agreements >nul 2>&1
            if !errorlevel! neq 0 (
                echo [WARN] winget failed for %%p
            )
        )
    ) else (
        echo [WARN] winget not found — please install manually:
        echo        scoop install mpv chafa
        echo        or winget install mpv chafa
    )
)

:: ── 3. Python 3.10+ ────────────────────────────────────────────
echo.
echo Resolving Python 3.10+ interpreter…

:: Try system python first
set "PYTHON_EXE="
for %%c in (python3 python py) do (
    where %%c >nul 2>nul
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%v in ('%%c --version 2^>nul') do (
            for /f "tokens=1,2 delims=." %%a in ("%%v") do (
                if %%a geq 3 (
                    if %%b geq 10 (
                        for /f "delims=" %%p in ('where %%c') do set "PYTHON_EXE=%%p"
                    )
                )
            )
        )
    )
    if defined PYTHON_EXE goto :python_found
)

:: Fallback: uv-managed Python
echo Python 3.10+ not found on system — checking uv-managed interpreters…
for /f "usebackq delims=" %%I in (`uv python find 3.10 2^>nul`) do set "PYTHON_EXE=%%I"
if not defined PYTHON_EXE (
    echo Installing Python 3.10 via uv…
    uv python install 3.10
    for /f "usebackq delims=" %%I in (`uv python find 3.10 2^>nul`) do set "PYTHON_EXE=%%I"
)

:python_found
if not defined PYTHON_EXE (
    echo [ERROR] Python 3.10+ required — install it and re-run setup.
    exit /b 1
)
echo ^> Python %PYTHON_EXE%

:: ── 4. Global install ─────────────────────────────────────────
echo.
echo Globally installing yt-tui…
uv tool install . --python "%PYTHON_EXE%"

:: ── 5. Download quality config ────────────────────────────────────
echo.
echo --- Download Quality ---
echo Pick video and audio quality separately.
echo If your chosen quality isn't available, it falls back to the best available.
echo.

:: ── Video quality ──
echo Select VIDEO quality (press Enter for default 1080p):
echo   1) 4K     (2160p) - best up to 4K
echo   2) 1440p          - best up to 1440p
echo   3) 1080p          - best up to 1080p  (default)
echo   4) 720p           - best up to 720p
echo   5) 480p           - best up to 480p
echo   6) 360p           - best up to 360p
echo   7) Best  (no cap) - highest available
echo   q) Skip           - keep 1080p default
echo.
set /p video_choice=Video choice [3/q]:

if "%video_choice%"=="1" set "height=2160"
if "%video_choice%"=="2" set "height=1440"
if "%video_choice%"=="3" set "height=1080"
if "%video_choice%"=="4" set "height=720"
if "%video_choice%"=="5" set "height=480"
if "%video_choice%"=="6" set "height=360"
if "%video_choice%"=="7" set "height="
if "%video_choice%"=="" set "height=1080"

:: ── Audio quality ──
echo.
echo Select AUDIO quality (press Enter for default Best):
echo   1) 320 kbps  - best audio up to 320kbps
echo   2) 256 kbps  - best audio up to 256kbps
echo   3) 192 kbps  - best audio up to 192kbps
echo   4) 128 kbps  - best audio up to 128kbps
echo   5) Best      - highest available  (default)
echo   q) Skip      - keep default
echo.
set /p audio_choice=Audio choice [5/q]:

if "%audio_choice%"=="1" set "abr=320"
if "%audio_choice%"=="2" set "abr=256"
if "%audio_choice%"=="3" set "abr=192"
if "%audio_choice%"=="4" set "abr=128"
if "%audio_choice%"=="5" set "abr="
if "%audio_choice%"=="" set "abr="

:: ── Build the format string ──
:: Nest if-defined checks so both "video only" and "audio only" paths work.
if defined height (
    if defined abr (
        set "quality_val=bestvideo[height<=%height%]+bestaudio[abr<=%abr%]/bestvideo+bestaudio/best"
    ) else (
        set "quality_val=bestvideo[height<=%height%]+bestaudio/bestvideo+bestaudio/best"
    )
) else if defined abr (
    set "quality_val=bestvideo+bestaudio[abr<=%abr%]/bestvideo+bestaudio/best"
)
:: If neither height nor abr was set, quality_val stays undefined → use default

if defined quality_val (
    echo.
    echo Setting user environment variable YT_TUI_QUALITY=%quality_val%
    setx YT_TUI_QUALITY "%quality_val%" >nul
    if !errorlevel! equ 0 (
        echo Done! Restart your terminal for the change to take effect.
    ) else (
        echo [WARN] setx failed. Add manually:
        echo   setx YT_TUI_QUALITY "%quality_val%"
    )
) else (
    echo.
    echo Using default quality ^(no env var set^)
    echo Default: 1080p video + best audio
)

echo.
echo === Done ===
echo Run from anywhere:  yt-tui
echo Incognito mode:     yt-tui incog
if defined quality_val (
    for %%h in (%height%) do (if "%%h"=="" (set vdisp=best) else set vdisp=%%h)
    for %%a in (%abr%) do (if "%%a"=="" (set adisp=best) else set adisp=%%a)
    echo Current quality: !vdisp!p video + !adisp! kbps audio
) else (
    echo Download quality: 1080p video + best audio ^(default^)
)
echo Change quality:     setx YT_TUI_QUALITY "format-string"
