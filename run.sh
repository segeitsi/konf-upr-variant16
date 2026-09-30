#!/bin/sh
# Запуск из любой рабочей директории.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec "${PYTHON:-python3}" -m src
