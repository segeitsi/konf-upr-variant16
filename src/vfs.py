import base64
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
import posixpath
import stat
import zipfile

ZIP_MODE_SHIFT = 16


class VFSError(ValueError):
    pass


@dataclass
class Node:

    directory: bool
    content: str = ""
    modified: datetime = field(default_factory=datetime.now)

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
                for info in archive.infolist():
                    fs._load_entry(archive, info)
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            raise VFSError(f"Ошибка загрузки VFS {path}: {error}") from error
        except (NotImplementedError, ValueError) as error:
            raise VFSError(f"Неверный формат VFS {path}: {error}") from error
        return fs

    def _entry_path(self, info) -> str:
        name = info.filename
        parts = PurePosixPath(name).parts
        if not name or name.startswith("/") or ".." in parts:
            raise VFSError(f"Недопустимый путь в ZIP: {name!r}")
        if "\\" in name or "\x00" in name:
            raise VFSError(f"Недопустимый путь в ZIP: {name!r}")
        if stat.S_ISLNK(info.external_attr >> ZIP_MODE_SHIFT):
            raise VFSError(f"Символические ссылки не поддерживаются: {name}")
        return self.resolve(name)

    def _load_entry(self, archive, info) -> None:
        path = self._entry_path(info)
        if path == "/":
            return
        parent = posixpath.dirname(path)
        self._ensure_directory(parent)
        old = self.nodes.get(path)
        if old and (not old.directory or not info.is_dir()):
            raise VFSError(f"Повторяющийся путь в ZIP: {info.filename}")
        payload = b"" if info.is_dir() else archive.read(info)
        self.nodes[path] = Node(
            info.is_dir(), base64.b64encode(payload).decode("ascii"),
            datetime(*info.date_time),
        )

    def _ensure_directory(self, path: str) -> None:
        if path == "/":
            return
        existing = self.nodes.get(path)
        if existing:
            if not existing.directory:
                raise VFSError(f"Файл использован как каталог: {path}")
            return
        self._ensure_directory(posixpath.dirname(path))
        self.nodes[path] = Node(directory=True)

    def resolve(self, path: str, cwd: str = "/") -> str:
        if not path:
            raise VFSError("Пустой путь.")
        return "/" + posixpath.normpath(posixpath.join(cwd, path)).lstrip("/")

    def get(self, path: str) -> Node:
        try:
            return self.nodes[path]
        except KeyError as error:
            raise VFSError(f"Путь не найден: {path}") from error

    def children(self, path: str) -> list[str]:
        if not self.get(path).directory:
            raise VFSError(f"Не каталог: {path}")
        return sorted(
            posixpath.basename(name) for name in self.nodes
            if name != "/" and posixpath.dirname(name) == path
        )

    def text(self, path: str) -> str:
        node = self.get(path)
        if node.directory:
            raise VFSError(f"Это каталог: {path}")
        try:
            return node.data().decode("utf-8")
        except UnicodeError as error:
            raise VFSError(f"Файл не является текстом UTF-8: {path}") from error
