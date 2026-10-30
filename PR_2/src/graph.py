from collections import deque
from dataclasses import dataclass, field

from .errors import AppError
from .requirements import normalize
from .versions import matches

MAX_PACKAGES = 1000


@dataclass
class Graph:
    root: str
    edges: dict = field(default_factory=dict)
    versions: dict = field(default_factory=dict)
    bfs: list = field(default_factory=list)

    def label(self, name):
        return f'{name}=={self.versions[name]}'


def build_graph(repository, name, version, test=False):
    root = name if test else normalize(name)
    graph = Graph(root, versions={root: version})
    extras = {root: set()}
    queue = deque([root])
    visited = set()
    while queue:
        current = queue.popleft()
        signature = current, frozenset(extras[current])
        if signature in visited:
            continue
        visited.add(signature)
        if current not in graph.edges:
            graph.edges[current] = []
            graph.bfs.append(current)
        dependencies = repository.dependencies(
            current, graph.versions[current], extras[current],
        )
        for requirement in dependencies:
            _connect(graph, current, requirement, repository, extras, queue)
    return graph


def _connect(graph, parent, requirement, repository, extras, queue):
    child = requirement.name
    if child not in graph.versions:
        if len(graph.versions) >= MAX_PACKAGES:
            raise AppError(f"Граф превысил лимит {MAX_PACKAGES} пакетов.")
        graph.versions[child] = repository.resolve(requirement)
        extras[child] = set(requirement.extras)
        queue.append(child)
    elif not matches(graph.versions[child], requirement.specifier):
        selected = graph.label(child)
        raise AppError(f"Конфликт версий: {selected}, требуется {requirement}")
    if not requirement.extras.issubset(extras[child]):
        extras[child].update(requirement.extras)
        queue.append(child)
    if child not in graph.edges[parent]:
        graph.edges[parent].append(child)


def describe_graph(graph):
    lines = ['BFS: ' + ' -> '.join(graph.bfs)]
    for name in graph.bfs:
        children = ', '.join(graph.label(child) for child in graph.edges[name])
        lines.append(f'{graph.label(name)}: {children or "(нет зависимостей)"}')
    return '\n'.join(lines)
