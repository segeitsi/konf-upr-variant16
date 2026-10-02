"""Разбор и выполнение команд"""

import json
import shlex
from dataclasses import dataclass


class CommandError(ValueError):
    """Ошибка ввода команды, которую следует показать пользователю."""


@dataclass(frozen=True)
class CommandResult:
    """Текст результата и признак завершения приложения."""

    output: str = ""
    should_exit: bool = False


def parse_command(line: str) -> list[str]:
    """Разобрать строку, сохранив аргументы в кавычках целиком."""
    try:
        return shlex.split(line, comments=False, posix=True)
    except ValueError as error:
        raise CommandError(
            "Не удалось разобрать команду: проверьте кавычки "
            "и символы экранирования."
        ) from error


def execute_command(line: str) -> CommandResult:
    """Выполнить команду этапа 1; пустая строка ничего не делает."""
    tokens = parse_command(line)
    if not tokens:
        return CommandResult()
    command, *arguments = tokens
    if command == "exit":
        if arguments:
            raise CommandError("Команда exit не принимает аргументы.")
        return CommandResult("Завершение работы.", should_exit=True)
    if command not in {"ls", "cd"}:
        raise CommandError(f"Неизвестная команда: {command!r}.")
    if command == "cd" and len(arguments) > 1:
        raise CommandError("Использование: cd [путь].")
    formatted = json.dumps(arguments, ensure_ascii=False)
    return CommandResult(
        f"Команда: {command}\nАргументы: {formatted}"
    )
