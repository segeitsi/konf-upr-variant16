#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
./run.sh --stage 1 --package requests --version 2.32.3
for graph in single chain diamond cycle; do
    ./run.sh --stage 3 --test --repository "examples/$graph.json" \
        --package A --version 1.0
    ./run.sh --stage 5 --test --repository "examples/$graph.json" \
        --package A --version 1.0 --ascii-tree
done
./run.sh --stage 4 --test --repository examples/diamond.json \
    --package A --version 1.0
if ./run.sh --stage 4 --test --repository examples/cycle.json \
    --package A --version 1.0; then
    echo 'Ожидалась ошибка цикла' >&2
    exit 1
fi
