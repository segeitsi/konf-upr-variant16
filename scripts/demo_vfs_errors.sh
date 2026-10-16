#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"${PYTHON:-python3}" -B scripts/generate_vfs.py data
./run.sh --vfs data/invalid.zip --startup scripts/stage3.txt
./run.sh --vfs data/missing.zip --startup scripts/stage3.txt
