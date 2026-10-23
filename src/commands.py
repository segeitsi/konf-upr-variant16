import calendar
from datetime import date
import posixpath
import stat

from .shell import CommandError, CommandResult, parse_command
from .vfs import VirtualFS, VFSError

MAX_CD_ARGS = 1
SINGLE_PATH_COUNT = 1
DEFAULT_TAIL_LINES = 10
YEAR_ONLY_ARGS = 1
MAX_CAL_ARGS = 2
MIN_MONTH, MAX_MONTH = 1, 12
MIN_YEAR, MAX_YEAR = 1, 9999
LS_FLAGS = ("-a", "-l", "-al", "-la")
LS_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def split_arguments(arguments, allowed_flags=()):
    flags = set()
    paths = []
    read_flags = True

    for argument in arguments:
        if read_flags and argument == "--":
            read_flags = False
            continue

        if read_flags and argument.startswith("-"):
            if argument not in allowed_flags:
                raise VFSError(f"Неизвестный параметр: {argument}")
            flags.add(argument)
        else:
            paths.append(argument)

    return flags, paths


class Shell:
    def __init__(self, fs: VirtualFS | None = None) -> None:
        if fs is None:
            fs = VirtualFS()
        self.fs = fs
        self.cwd = "/"

    def execute(self, line: str) -> CommandResult:
        words = parse_command(line)
        if not words:
            return CommandResult()

        command = words[0]
        arguments = words[1:]
        if command == "exit":
            if arguments:
                raise CommandError("Команда exit не принимает аргументы.")
            return CommandResult("Завершение работы.", should_exit=True)

        commands = {
            "ls": self.ls,
            "cd": self.cd,
            "tail": self.tail,
            "cal": self.cal,
            "touch": self.touch,
            "rmdir": self.rmdir,
        }
        handler = commands.get(command)
        if handler is None:
            raise CommandError(f"Неизвестная команда: {command!r}.")

        try:
            output = handler(arguments)
        except VFSError as error:
            raise CommandError(str(error)) from error
        return CommandResult(output)

    def ls(self, arguments) -> str:
        flags, paths = split_arguments(arguments, allowed_flags=LS_FLAGS)
        if not paths:
            paths = ["."]

        show_hidden = False
        detailed = False
        for flag in flags:
            if "a" in flag:
                show_hidden = True
            if "l" in flag:
                detailed = True
        several_paths = len(paths) > SINGLE_PATH_COUNT
        output = []
        for name in paths:
            path = self.fs.resolve(name, self.cwd)
            listing = self._list_path(path, show_hidden, detailed)
            if several_paths:
                listing = f"{name}:\n{listing}"
            output.append(listing)
        return "\n\n".join(output)

    def _list_path(self, path, show_hidden, detailed=False) -> str:
        node = self.fs.get(path)
        if not node.directory:
            return self._format_entry(path, posixpath.basename(path), detailed)

        names = self.fs.children(path)
        if show_hidden:
            names = [".", ".."] + names

        output = []
        for name in names:
            if name.startswith(".") and not show_hidden:
                continue
            child_path = self.fs.resolve(name, path)
            output.append(self._format_entry(child_path, name, detailed))
        return "\n".join(output)

    def _format_entry(self, path, name, detailed) -> str:
        node = self.fs.get(path)
        if node.directory and name not in {".", ".."}:
            name += "/"
        if not detailed:
            return name

        size = 0
        if not node.directory:
            size = len(node.data())
        permissions = stat.filemode(node.mode)
        modified = node.modified.strftime(LS_TIME_FORMAT)
        return f"{permissions} {size:>8} {modified} {name}"

    def cd(self, arguments) -> str:
        _, paths = split_arguments(arguments)
        if len(paths) > MAX_CD_ARGS:
            raise VFSError("Использование: cd [путь].")

        path = "/"
        if paths:
            path = self.fs.resolve(paths[0], self.cwd)
        if not self.fs.get(path).directory:
            raise VFSError(f"Не каталог: {path}")
        self.cwd = path
        return ""

    def _parse_tail_args(self, arguments):
        arguments = list(arguments)
        count_text = str(DEFAULT_TAIL_LINES)

        if arguments and arguments[0].startswith("-n"):
            option = arguments.pop(0)
            count_text = option.removeprefix("-n")
            if option == "-n":
                if not arguments:
                    raise VFSError("После -n требуется число строк.")
                count_text = arguments.pop(0)

        count = self._parse_tail_count(count_text)
        _, paths = split_arguments(arguments)
        if not paths:
            raise VFSError("Использование: tail [-n N] файл [файлы…].")
        from_start = count_text.startswith("+")
        return count, from_start, paths

    def _parse_tail_count(self, text) -> int:
        digits = text
        if text.startswith(("+", "-")):
            digits = text[1:]

        message = "Количество строк tail должно быть целым."
        if not digits.isascii() or not digits.isdecimal():
            raise VFSError(message)
        try:
            return abs(int(text))
        except ValueError as error:
            raise VFSError(message) from error

    def tail(self, arguments) -> str:
        count, from_start, paths = self._parse_tail_args(arguments)
        several_files = len(paths) > SINGLE_PATH_COUNT
        output = []

        for name in paths:
            path = self.fs.resolve(name, self.cwd)
            text = self._tail_text(path, count, from_start)
            if several_files:
                text = f"==> {name} <==\n{text}"
            output.append(text)
        return "\n\n".join(output)

    def _tail_text(self, path, count, from_start) -> str:
        content = self.fs.text(path)
        lines = content.split("\n")
        if content.endswith("\n"):
            lines.pop()

        if from_start:
            first_line = max(count - 1, 0)
            lines = lines[first_line:]
        elif count:
            lines = lines[-count:]
        else:
            lines = []
        return "\n".join(lines)

    def cal(self, arguments) -> str:
        if len(arguments) > MAX_CAL_ARGS:
            raise VFSError("Использование: cal [год | месяц год].")

        today = date.today()
        month = today.month
        year = today.year
        whole_year = False
        try:
            if len(arguments) == YEAR_ONLY_ARGS:
                year = int(arguments[0])
                whole_year = True
            elif arguments:
                month = int(arguments[0])
                year = int(arguments[1])
        except ValueError as error:
            raise VFSError("Месяц и год должны быть целыми числами.") from error

        if not MIN_YEAR <= year <= MAX_YEAR:
            raise VFSError("Год должен быть от 1 до 9999.")

        printer = calendar.TextCalendar(firstweekday=calendar.SUNDAY)
        if whole_year:
            return printer.formatyear(year).rstrip()
        if not MIN_MONTH <= month <= MAX_MONTH:
            raise VFSError("Месяц должен быть от 1 до 12.")
        return printer.formatmonth(year, month).rstrip()


    def touch(self, arguments) -> str:
        _, paths = split_arguments(arguments)
        if not paths:
            raise VFSError("Использование: touch путь [пути…].")

        for path in paths:
            self.fs.touch(path, self.cwd)
        return ""

    def rmdir(self, arguments) -> str:
        _, paths = split_arguments(arguments)
        if not paths:
            raise VFSError("Использование: rmdir каталог [каталоги…].")

        for path in paths:
            self.fs.rmdir(path, self.cwd)
        return ""
