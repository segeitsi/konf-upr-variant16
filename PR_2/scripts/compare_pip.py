import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.graph import build_graph
from src.order import dependency_order
from src.render import to_ascii, to_d2
from src.repository import PyPIRepository
from src.requirements import normalize, parse_requirement


def reference_data(report, inspection):
    versions = {normalize(item['metadata']['name']): item['metadata']['version']
                for item in report['install']}
    edges = set()
    for item in inspection['installed']:
        info = item['metadata']
        parent = normalize(info['name'])
        if parent not in versions:
            continue
        for text in info.get('requires_dist', []):
            req = parse_requirement(text)
            if req.applies() and req.name in versions:
                edges.add((parent, req.name))
    return versions, edges


def write_results(args, graph, report, inspection):
    versions, edges = reference_data(report, inspection)
    actual_edges = {(name, child) for name, children in graph.edges.items()
                    for child in children}
    order = dependency_order(graph)
    log = args.log.read_text()
    marker = 'Installing collected packages: '
    pip_order = next(line.split(marker)[1].split(', ')
                     for line in log.splitlines() if marker in line)
    pip_order = [normalize(name.strip()) for name in pip_order]
    valid_order = all(pip_order.index(child) < pip_order.index(parent)
                      for parent, child in edges)
    if versions != graph.versions or edges != actual_edges or not valid_order:
        raise ValueError('Результаты не совпали с pip; проверьте данные.')
    folder = args.output
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{args.package}.d2').write_text(to_d2(graph) + '\n')
    (folder / f'{args.package}.txt').write_text(to_ascii(graph) + '\n')
    text = comparison_text(args, graph, order, pip_order, report)
    (folder / f'{args.package}-comparison.md').write_text(text)
    print(text)


def comparison_text(args, graph, order, pip_order, report):
    own = ' → '.join(order)
    reference = ' → '.join(pip_order)
    return (
        f'# {args.package}=={args.version}\n\n'
        f'Проверено {datetime.now():%Y-%m-%d}, Python '
        f'{report["environment"]["python_full_version"]}, '
        f'pip {report["pip_version"]}.\n\n'
        f'Узлов: {len(graph.edges)}. Версии и рёбра совпали с '
        'планом pip и метаданными `pip inspect`.\n\n'
        f'Наш порядок: {own}.\n\nПорядок установки pip: {reference}.\n\n'
        'В обоих порядках зависимости идут раньше зависящих от них '
        'пакетов. Порядок независимых узлов может различаться.\n'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', required=True)
    parser.add_argument('--version', required=True)
    for name in ['report', 'inspect', 'log']:
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('examples'))
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    inspection = json.loads(args.inspect.read_text())
    graph = build_graph(PyPIRepository('https://pypi.org'),
                        args.package, args.version)
    write_results(args, graph, report, inspection)


if __name__ == '__main__':
    main()
