import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlsplit

from .errors import AppError
from .versions import Version

NAME_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
VERSION_PATTERN = r"[A-Za-z0-9][A-Za-z0-9.!+_-]*"
FIRST_STAGE, LAST_STAGE = 1, 5


@dataclass(frozen=True)
class Config:
    package: str
    repository: str
    test: bool
    version: str
    ascii_tree: bool
    stage: int

    def describe(self):
        return "\n".join([
            f"package={self.package}", f"repository={self.repository}",
            f"test={str(self.test).lower()}", f"version={self.version}",
            f"ascii_tree={str(self.ascii_tree).lower()}",
            f"stage={self.stage}",
        ])


def validate_repository(value, test):
    if test:
        path = Path(value)
        if not path.is_file():
            raise AppError(f"Тестовый репозиторий не найден: {value}")
        try:
            path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise AppError(f"Нельзя прочитать репозиторий: {error}") from error
        return
    validate_url(value)


def validate_url(value):
    if any(character.isspace() for character in value):
        raise AppError("URL репозитория не должен содержать пробелы.")
    url = urlsplit(value)
    if url.scheme not in {"http", "https"} or not url.hostname:
        raise AppError("Репозиторий: нужен URL http:// или https://.")
    if url.query or url.fragment or url.username or url.password:
        raise AppError("URL не должен содержать логин, параметры или #.")
    try:
        url.port
    except ValueError as error:
        raise AppError("Неверный порт в URL репозитория.") from error


def parse_config(arguments=None):
    parser = argparse.ArgumentParser(
        description="Граф зависимостей Python-пакетов, вариант 16.",
    )
    parser.add_argument("--package", required=True, help="Имя пакета")
    parser.add_argument("--version", required=True, help="Версия пакета")
    parser.add_argument("--repository", default="https://pypi.org",
                        help="URL PyPI JSON API или путь к JSON")
    parser.add_argument("--test", action="store_true", help="Тестовый JSON")
    parser.add_argument("--ascii-tree", action="store_true",
                        help="Также вывести ASCII-дерево")
    parser.add_argument("--stage", type=int, default=LAST_STAGE,
                        choices=range(FIRST_STAGE, LAST_STAGE + 1))
    config = Config(**vars(parser.parse_args(arguments)))
    try:
        validate_config(config)
    except (AppError, ValueError) as error:
        parser.error(str(error))
    return config


def validate_config(config):
    if re.fullmatch(NAME_PATTERN, config.package) is None:
        raise AppError("Неверное имя пакета.")
    if re.fullmatch(VERSION_PATTERN, config.version) is None:
        raise AppError("Неверная версия пакета.")
    Version(config.version)
    validate_repository(config.repository, config.test)
    if config.test and re.fullmatch(r"[A-Z]+", config.package) is None:
        raise AppError("В тестовом режиме имя состоит из букв A-Z.")
