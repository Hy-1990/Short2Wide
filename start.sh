#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

for dependency in python3 ffmpeg ffprobe; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "Missing dependency: $dependency. Install it first; see README.md." >&2
        exit 1
    fi
done

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else "Python 3.10+ is required.")'

if ! python3 -c 'import requests, yt_dlp' 2>/dev/null; then
    echo "Install dependencies first: python3 -m pip install -r requirements.txt" >&2
    exit 1
fi

exec python3 -B server.py "$@"
