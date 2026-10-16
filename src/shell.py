import shlex
from dataclasses import dataclass


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
    from .commands import Shell

    return Shell().execute(line)
