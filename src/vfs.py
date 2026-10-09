"""Виртуальная файловая система ZIP, хранящаяся в памяти."""

import base64
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
import posixpath
import zipfile


class VFSError(ValueError):
    """Ошибка загрузки или операции с виртуальным путём."""


@dataclass
class Node:
    """Каталог или файл; содержимое файла закодировано в base64."""

    directory: bool
    content: str = ""
    modified: datetime = field(default_factory=datetime.now)

    def data(self) -> bytes:
        """Вернуть исходные байты файла."""
        return base64.b64decode(self.content)


class VirtualFS:
    """Дерево виртуальных узлов; оригинальный архив остаётся неизменным."""

    def __init__(self) -> None:
        """Создать пустую файловую систему с корнем."""
        self.nodes = {"/": Node(directory=True)}

    @classmethod
    def load(cls, path: Path) -> "VirtualFS":
        """Прочитать ZIP без распаковки и проверить структуру путей."""
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

    def _load_entry(self, archive, info) -> None:
        """Добавить запись ZIP и её родительские каталоги."""
        name = info.filename
        parts = PurePosixPath(name).parts
        if not name or name.startswith("/") or ".." in parts:
            raise VFSError(f"Недопустимый путь в ZIP: {name!r}")
        if "\\" in name or "\x00" in name:
            raise VFSError(f"Недопустимый путь в ZIP: {name!r}")
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise VFSError(f"Символические ссылки не поддерживаются: {name}")
        path = self.resolve(name)
        if path == "/":
            return
        parent = posixpath.dirname(path)
        self._ensure_directory(parent)
        old = self.nodes.get(path)
        if old and (not old.directory or not info.is_dir()):
            raise VFSError(f"Повторяющийся путь в ZIP: {name}")
        payload = b"" if info.is_dir() else archive.read(info)
        self.nodes[path] = Node(
            info.is_dir(), base64.b64encode(payload).decode("ascii"),
            datetime(*info.date_time),
        )

    def _ensure_directory(self, path: str) -> None:
        """Создать отсутствующих родителей при загрузке архива."""
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
        """Нормализовать абсолютный или относительный виртуальный путь."""
        if not path:
            raise VFSError("Пустой путь.")
        return "/" + posixpath.normpath(posixpath.join(cwd, path)).lstrip("/")

    def get(self, path: str) -> Node:
        """Получить узел или сообщить об отсутствующем пути."""
        try:
            return self.nodes[path]
        except KeyError as error:
            raise VFSError(f"Путь не найден: {path}") from error

    def children(self, path: str) -> list[str]:
        """Вернуть имена непосредственных дочерних узлов каталога."""
        if not self.get(path).directory:
            raise VFSError(f"Не каталог: {path}")
        return sorted(
            posixpath.basename(name) for name in self.nodes
            if name != "/" and posixpath.dirname(name) == path
        )

    def text(self, path: str) -> str:
        """Прочитать UTF-8 файл; двоичные данные не выводятся как текст."""
        node = self.get(path)
        if node.directory:
            raise VFSError(f"Это каталог: {path}")
        try:
            return node.data().decode("utf-8")
        except UnicodeError as error:
            raise VFSError(f"Файл не является текстом UTF-8: {path}") from error
