"""Выполнение стартового скрипта с остановкой на первой ошибке."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .shell import CommandError, execute_command

WriteOutput = Callable[[str, str], None]


@dataclass(frozen=True)
class StartupResult:
    """Признаки ошибки скрипта и завершения эмулятора."""

    failed: bool = False
    should_exit: bool = False


def run_startup(
    path: Path, write: WriteOutput, prompt: str,
) -> StartupResult:
    """Показать диалог скрипта и остановиться на первой ошибке."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        write(f"Ошибка чтения стартового скрипта {path}: {error}", "error")
        return StartupResult(failed=True)
    write(f"Стартовый скрипт: {path}", "")
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        write(f"{prompt} {line}", "prompt")
        try:
            result = execute_command(line)
        except CommandError as error:
            write(
                f"Ошибка в скрипте {path}, строка {number}: {error}\n"
                "Выполнение скрипта остановлено.",
                "error",
            )
            return StartupResult(failed=True)
        if result.output:
            write(result.output, "")
        if result.should_exit:
            return StartupResult(should_exit=True)
    write("Стартовый скрипт завершён.", "")
    return StartupResult()
