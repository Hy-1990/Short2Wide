#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

for dependency in ffmpeg ffprobe; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "Missing dependency: $dependency. Install it first; see README.md." >&2
        exit 1
    fi
done

short2wide_python=''
# An active conda environment may shadow a Homebrew Python with ready packages.
for candidate in python3 python /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1 &&
        "$candidate" -c 'import sys, requests, yt_dlp; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
        short2wide_python=$(command -v "$candidate")
        break
    fi
done

if [[ -z "$short2wide_python" ]]; then
    echo "No Python 3.10+ with requests and yt-dlp was found." >&2
    echo "Install dependencies in the Python you use: python3 -m pip install -r requirements.txt" >&2
    exit 1
fi

"$short2wide_python" -c 'import sys; print("Using Python: " + sys.executable, flush=True)'
exec "$short2wide_python" -B server.py "$@"
