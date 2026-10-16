#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"${PYTHON:-python3}" -B scripts/generate_vfs.py data
for command in ls cd tail cal touch rmdir; do
    ./run.sh --vfs data/nested.zip --startup "scripts/error_$command.txt"
done
