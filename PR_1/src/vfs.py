import base64
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
import posixpath
import stat
import zipfile

ZIP_MODE_SHIFT = 16
DEFAULT_FILE_MODE = stat.S_IFREG | 0o644
DEFAULT_DIRECTORY_MODE = stat.S_IFDIR | 0o755


class VFSError(ValueError):
    pass


@dataclass
class Node:
    directory: bool
    content: str = ""
    modified: datetime = field(default_factory=datetime.now)
    mode: int = 0

    def __post_init__(self) -> None:
        if not self.mode:
            self.mode = DEFAULT_FILE_MODE
            if self.directory:
                self.mode = DEFAULT_DIRECTORY_MODE

    def data(self) -> bytes:
        return base64.b64decode(self.content)


class VirtualFS:
    def __init__(self) -> None:
        self.nodes = {"/": Node(directory=True)}

    @classmethod
    def load(cls, path: Path) -> "VirtualFS":
        fs = cls()
        try:
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    fs._load_entry(archive, entry)
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            raise VFSError(f"Ошибка загрузки VFS {path}: {error}") from error
        except (NotImplementedError, ValueError) as error:
            raise VFSError(f"Неверный формат VFS {path}: {error}") from error
        return fs

    def _entry_path(self, entry) -> str:
        name = entry.filename
        parts = PurePosixPath(name).parts
        if not name or name.startswith("/") or ".." in parts:
            raise VFSError(f"Недопустимый путь в ZIP: {name!r}")
        if "\\" in name or "\x00" in name:
            raise VFSError(f"Недопустимый путь в ZIP: {name!r}")

        mode = entry.external_attr >> ZIP_MODE_SHIFT
        if stat.S_ISLNK(mode):
            raise VFSError(f"Символические ссылки не поддерживаются: {name}")
        return self.resolve(name)

    def _load_entry(self, archive, entry) -> None:
        path = self._entry_path(entry)
        if path == "/":
            return

        parent = posixpath.dirname(path)
        self._ensure_directory(parent)
        is_directory = entry.is_dir()
        existing = self.nodes.get(path)
        if existing is not None:
            if not existing.directory or not is_directory:
                raise VFSError(f"Повторяющийся путь в ZIP: {entry.filename}")

        data = b""
        if not is_directory:
            data = archive.read(entry)
        content = base64.b64encode(data).decode("ascii")
        mode = entry.external_attr >> ZIP_MODE_SHIFT
        if mode and not stat.S_IFMT(mode):
            if is_directory:
                mode |= stat.S_IFDIR
            else:
                mode |= stat.S_IFREG
        self.nodes[path] = Node(
            directory=is_directory,
            content=content,
            modified=datetime(*entry.date_time),
            mode=mode,
        )

    def _ensure_directory(self, path: str) -> None:
        missing = []
        current = path
        while current not in self.nodes:
            missing.append(current)
            current = posixpath.dirname(current)

        if not self.nodes[current].directory:
            raise VFSError(f"Файл использован как каталог: {current}")
        for directory in reversed(missing):
            self.nodes[directory] = Node(directory=True)

    def resolve(self, path: str, cwd: str = "/") -> str:
        if not path:
            raise VFSError("Пустой путь.")
        if "\x00" in path:
            raise VFSError("Нулевой символ в пути.")
        full_path = posixpath.join(cwd, path)
        normalized = posixpath.normpath(full_path)
        return "/" + normalized.lstrip("/")

    def get(self, path: str) -> Node:
        node = self.nodes.get(path)
        if node is None:
            raise VFSError(f"Путь не найден: {path}")
        return node

    def children(self, path: str) -> list[str]:
        if not self.get(path).directory:
            raise VFSError(f"Не каталог: {path}")

        names = []
        for child_path in self.nodes:
            if child_path == "/":
                continue
            parent = posixpath.dirname(child_path)
            if parent == path:
                names.append(posixpath.basename(child_path))
        return sorted(names)

    def text(self, path: str) -> str:
        node = self.get(path)
        if node.directory:
            raise VFSError(f"Это каталог: {path}")
        try:
            return node.data().decode("utf-8")
        except UnicodeError as error:
            raise VFSError(f"Файл не является текстом UTF-8: {path}") from error


    def _mutation_path(self, path: str, cwd: str) -> str:
        target = self.resolve(path, cwd)
        current = cwd
        if path.startswith("/"):
            current = "/"

        parent_parts = path.split("/")[:-1]
        for part in parent_parts:
            if not part:
                part = "."
            current = self.resolve(part, current)
            if not self.get(current).directory:
                raise VFSError(f"Не каталог: {current}")
        return target

    def touch(self, path: str, cwd: str = "/") -> None:
        target = self._mutation_path(path, cwd)
        if target in self.nodes:
            self.nodes[target].modified = datetime.now()
            return

        parent = posixpath.dirname(target)
        if not self.get(parent).directory:
            raise VFSError(f"Не каталог: {parent}")
        self.nodes[target] = Node(directory=False)

    def rmdir(self, path: str, cwd: str = "/") -> None:
        target = self._mutation_path(path, cwd)
        name = posixpath.basename(path.rstrip("/"))
        if name in {".", ".."}:
            raise VFSError("Нельзя удалить каталог с именем '.' или '..'.")
        if target == "/":
            raise VFSError("Нельзя удалить корень VFS.")
        if not self.get(target).directory:
            raise VFSError(f"Не каталог: {target}")

        current_is_inside = cwd.startswith(target + "/")
        if cwd == target or current_is_inside:
            raise VFSError("Нельзя удалить текущий каталог или его родителя.")
        if self.children(target):
            raise VFSError(f"Каталог не пуст: {target}")
        del self.nodes[target]
