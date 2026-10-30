#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"${PYTHON:-python3}" -B scripts/generate_vfs.py data
./run.sh --vfs data/nested.zip --startup scripts/stage5.txt
for mode in touch rmdir rmdir_missing rmdir_file rmdir_root rmdir_current; do
    ./run.sh --vfs data/nested.zip --startup "scripts/error_$mode.txt"
done
