#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec ./run.sh --vfs "data/Моя VFS.zip" --startup scripts/success.txt
