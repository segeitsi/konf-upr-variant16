import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    vfs_path: Path | None = None
    startup_path: Path | None = None

    @property
    def vfs_name(self) -> str:
        if self.vfs_path is None:
            return "MyVFS"
        return self.vfs_path.name

    def describe(self) -> str:
        return (
            "Конфигурация:\n"
            f"  VFS: {self.vfs_path or 'не задана'}\n"
            f"  Стартовый скрипт: {self.startup_path or 'не задан'}"
        )


def parse_config(arguments: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки, вариант 16, этап 3.",
    )
    parser.add_argument(
        "--vfs", type=Path, metavar="PATH",
        help="путь к ZIP с VFS",
    )
    parser.add_argument(
        "--startup", type=Path, metavar="PATH",
        help="путь к стартовому скрипту с командами эмулятора",
    )
    options = parser.parse_args(arguments)
    return Config(options.vfs, options.startup)
