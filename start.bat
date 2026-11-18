@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"

python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 (
    set "SHORT2WIDE_PYTHON=python"
    goto :dependencies
)
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 (
    echo Python 3.10+ is required. Install Python and reopen your terminal.
    goto :error
)
set "SHORT2WIDE_PYTHON=py -3"

:dependencies
for %%T in (ffmpeg ffprobe) do (
    where %%T >nul 2>&1
    if errorlevel 1 (
        echo Missing %%T. Install FFmpeg and reopen your terminal. See README.md.
        goto :error
    )
)
%SHORT2WIDE_PYTHON% -c "import requests, yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo Install dependencies first: %SHORT2WIDE_PYTHON% -m pip install -r requirements.txt
    goto :error
)

%SHORT2WIDE_PYTHON% -B server.py %*
if errorlevel 1 goto :error
exit /b 0

:error
if not defined CI pause
exit /b 1
