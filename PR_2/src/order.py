from collections import deque

from .errors import AppError


def dependency_order(graph):
    pending = {name: len(children) for name, children in graph.edges.items()}
    parents = _parents(graph)
    ready = deque(sorted(name for name, count in pending.items() if not count))
    result = []
    while ready:
        current = ready.popleft()
        result.append(current)
        for parent in parents[current]:
            pending[parent] -= 1
            if not pending[parent]:
                ready.append(parent)
    if len(result) != len(graph.edges):
        blocked = ', '.join(name for name, count in pending.items() if count)
        raise AppError(f"Порядок невозможен: цикл блокирует узлы {blocked}")
    return result


def _parents(graph):
    parents = {name: [] for name in graph.edges}
    for name, children in graph.edges.items():
        for child in children:
            parents[child].append(name)
    return parents
