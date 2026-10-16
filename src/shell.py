import json
import shlex
from dataclasses import dataclass

MAX_CD_ARGS = 1


class CommandError(ValueError):
    pass


@dataclass(frozen=True)
class CommandResult:
    output: str = ""
    should_exit: bool = False


def parse_command(line: str) -> list[str]:
    try:
        return shlex.split(line, comments=False, posix=True)
    except ValueError as error:
        raise CommandError(
            "Не удалось разобрать команду: проверьте кавычки "
            "и символы экранирования."
        ) from error


def execute_command(line: str) -> CommandResult:
    words = parse_command(line)
    if not words:
        return CommandResult()

    command = words[0]
    arguments = words[1:]
    if command == "exit":
        if arguments:
            raise CommandError("Команда exit не принимает аргументы.")
        return CommandResult("Завершение работы.", should_exit=True)
    if command not in {"ls", "cd"}:
        raise CommandError(f"Неизвестная команда: {command!r}.")
    if command == "cd":
        if len(arguments) > MAX_CD_ARGS:
            raise CommandError("Использование: cd [путь].")

    arguments_text = json.dumps(arguments, ensure_ascii=False)
    output = f"Команда: {command}\nАргументы: {arguments_text}"
    return CommandResult(output)
