import json
from pathlib import Path
import re

from .errors import AppError
from .requirements import Requirement

TEST_NAME = re.compile(r'[A-Z]+')


class TestRepository:
    def __init__(self, path, version):
        self.version = version
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
        except (OSError, UnicodeError, ValueError) as error:
            raise AppError(f"Не удалось прочитать тестовый JSON: {error}")
        self.edges = self._validate(data)

    def _validate(self, data):
        if not isinstance(data, dict) or not data:
            raise AppError("Тестовый JSON должен быть непустым объектом.")
        for name, dependencies in data.items():
            self._check_name(name)
            if not isinstance(dependencies, list):
                raise AppError(f"{name}: зависимости должны быть списком.")
            for child in dependencies:
                self._check_name(child)
                if child not in data:
                    raise AppError(f"{name}: отсутствует пакет {child}")
        return {name: list(dict.fromkeys(children))
                for name, children in data.items()}

    def _check_name(self, name):
        if not isinstance(name, str) or TEST_NAME.fullmatch(name) is None:
            raise AppError(f"Неверное тестовое имя: {name!r}; нужны A-Z.")

    def dependencies(self, name, version, extras=()):
        if name not in self.edges:
            raise AppError(f"Пакет {name} отсутствует в тестовом репозитории.")
        if version != self.version:
            raise AppError(f"Нет тестовой версии {name}=={version}")
        return [Requirement(child) for child in self.edges[name]]

    def resolve(self, requirement):
        if requirement.name not in self.edges:
            raise AppError(f"Пакет {requirement.name} отсутствует.")
        return self.version
