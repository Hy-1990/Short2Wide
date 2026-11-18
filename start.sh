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

if [[ ! -x .venv/bin/python ]]; then
    echo "Creating Python environment..."
    python3 -m venv .venv
fi

echo "Checking Python dependencies (first run may download packages)..."
.venv/bin/python -m pip install --disable-pip-version-check --quiet -r requirements.txt

export PATH="$PWD/.venv/bin:$PATH"
exec .venv/bin/python -B server.py "$@"
