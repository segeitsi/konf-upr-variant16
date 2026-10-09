#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"${PYTHON:-python3}" -B scripts/generate_vfs.py data
exec ./run.sh --vfs "data/Моя VFS.zip" --startup scripts/success.txt
