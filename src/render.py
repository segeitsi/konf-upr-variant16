import json


def to_d2(graph):
    identifiers = {name: f'n{index}' for index, name in enumerate(graph.bfs)}
    lines = ['direction: right']
    for name in graph.bfs:
        label = json.dumps(graph.label(name), ensure_ascii=False)
        lines.append(f'{identifiers[name]}: {label}')
    for parent in graph.bfs:
        for child in graph.edges[parent]:
            lines.append(f'{identifiers[parent]} -> {identifiers[child]}')
    return '\n'.join(lines)


def to_ascii(graph):
    lines = [graph.label(graph.root)]
    expanded = {graph.root}
    stack = []
    _push_children(stack, graph, graph.root, '', frozenset({graph.root}))
    while stack:
        name, prefix, last, ancestors = stack.pop()
        branch = '`-- ' if last else '|-- '
        label = prefix + branch + graph.label(name)
        if name in ancestors:
            lines.append(label + ' [cycle]')
        elif name in expanded:
            lines.append(label + ' [already shown]')
        else:
            lines.append(label)
            expanded.add(name)
            child_prefix = prefix + ('    ' if last else '|   ')
            _push_children(stack, graph, name, child_prefix, ancestors | {name})
    return '\n'.join(lines)


def _push_children(stack, graph, name, prefix, ancestors):
    children = graph.edges[name]
    if not children:
        return
    last_child = children[-1]
    for child in reversed(children):
        stack.append((child, prefix, child == last_child, ancestors))
