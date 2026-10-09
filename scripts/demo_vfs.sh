#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"${PYTHON:-python3}" -B scripts/generate_vfs.py data
for archive in minimal files nested; do
    ./run.sh --vfs "data/$archive.zip" --startup scripts/stage3.txt
done
