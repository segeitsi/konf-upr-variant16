import sys

from .config import parse_config
from .errors import AppError
from .graph import build_graph, describe_graph
from .order import dependency_order
from .repository import PyPIRepository
from .test_repository import TestRepository

CONFIG_STAGE, DIRECT_STAGE, GRAPH_STAGE, ORDER_STAGE = 1, 2, 3, 4


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
        repository = TestRepository(config.repository, config.version)
    else:
        repository = PyPIRepository(config.repository)
    if config.stage == DIRECT_STAGE:
        print_direct(repository, config)
        return 0
    graph = build_graph(repository, config.package, config.version, config.test)
    if config.stage == ORDER_STAGE:
        order = dependency_order(graph)
        print('Порядок загрузки:')
        print(' -> '.join(graph.label(name) for name in order))
    else:
        print(describe_graph(graph))
    return 0


def print_direct(repository, config):
    dependencies = repository.dependencies(config.package, config.version)
    print(f"Прямые зависимости {config.package}=={config.version}:")
    for requirement in dependencies:
        print(requirement)
    if not dependencies:
        print('(нет зависимостей)')
