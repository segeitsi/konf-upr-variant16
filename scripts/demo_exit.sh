#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec ./run.sh --vfs data/demo.zip --startup scripts/exit.txt
