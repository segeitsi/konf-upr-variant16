import sys

from .config import parse_config
from .errors import AppError
from .repository import PyPIRepository

CONFIG_STAGE, DIRECT_STAGE = 1, 2


def main(arguments=None):
    config = parse_config(arguments)
    if config.stage == CONFIG_STAGE:
        print(config.describe())
        return 0
    try:
        return run(config)
    except AppError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


def run(config):
    if config.test:
        raise AppError("Тестовый граф доступен начиная с этапа 3.")
    repository = PyPIRepository(config.repository)
    dependencies = repository.dependencies(config.package, config.version)
    print(f"Прямые зависимости {config.package}=={config.version}:")
    for requirement in dependencies:
        print(requirement)
    if not dependencies:
        print('(нет зависимостей)')
    return 0
