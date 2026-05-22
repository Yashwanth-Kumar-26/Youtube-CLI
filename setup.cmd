@echo off
:: YT-TUI setup — Windows
:: Installs system deps via winget + uses uv to install yt-tui globally.
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
uv tool install .

echo.
echo === Done ===
echo Run from anywhere:  yt-tui
echo Incognito mode:     yt-tui incog

