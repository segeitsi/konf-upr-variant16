from pathlib import Path
import tempfile
import unittest

from src.errors import AppError
from src.graph import build_graph
from src.requirements import Requirement
from src.test_repository import TestRepository

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


class GraphTests(unittest.TestCase):
    def graph(self, filename):
        repo = TestRepository(EXAMPLES / filename, '1.0')
        return build_graph(repo, 'A', '1.0', test=True)

    def test_bfs_diamond_and_disconnected_package(self):
        graph = self.graph('diamond.json')
        self.assertEqual(graph.bfs, ['A', 'B', 'C', 'D'])
        self.assertEqual(graph.edges['B'], ['D'])
        self.assertEqual(graph.edges['C'], ['D'])
        self.assertNotIn('Z', graph.edges)

    def test_cycle_terminates_and_preserves_edge(self):
        graph = self.graph('cycle.json')
        self.assertEqual(graph.bfs, ['A', 'B', 'C'])
        self.assertEqual(graph.edges['C'], ['A'])

    def test_single_node(self):
        self.assertEqual(self.graph('single.json').edges, {'A': []})

    def test_long_chain_without_recursion(self):
        class Chain:
            def dependencies(self, name, version, extras):
                number = int(name)
                if number == last_node:
                    return []
                return [Requirement(str(number + 1))]
            def resolve(self, requirement):
                return '1.0'
        last_node = 899
        graph = build_graph(Chain(), '0', '1.0', test=True)
        self.assertEqual(len(graph.bfs), last_node + 1)

    def test_bad_test_graphs(self):
        cases = ['[]', '{}', '{"a": []}', '{"A": ["B"]}',
                 '{"A": "B"}', '{"A": [null]}', 'broken']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'graph.json'
            for text in cases:
                path.write_text(text)
                with self.subTest(text=text), self.assertRaises(AppError):
                    TestRepository(path, '1.0')

    def test_unknown_root(self):
        repo = TestRepository(EXAMPLES / 'single.json', '1.0')
        with self.assertRaises(AppError):
            build_graph(repo, 'Z', '1.0', test=True)

    def test_shared_constraint_conflict(self):
        class Conflicting:
            def dependencies(self, name, version, extras):
                return {'a': [Requirement('b'), Requirement('c')],
                        'b': [], 'c': [Requirement('b', '<2')]}[name]
            def resolve(self, requirement):
                return '3.0'
        with self.assertRaisesRegex(AppError, 'Конфликт версий'):
            build_graph(Conflicting(), 'a', '1.0')

    def test_later_extras_revisit_existing_node(self):
        class ExtraRepo:
            def dependencies(self, name, version, extras):
                data = {'a': [Requirement('b'), Requirement('c')],
                        'c': [Requirement('b', extras=frozenset({'tls'}))],
                        'b': [], 'd': []}
                if name == 'b' and 'tls' in extras:
                    return [Requirement('d')]
                return data[name]
            def resolve(self, requirement):
                return '1.0'
        graph = build_graph(ExtraRepo(), 'a', '1.0')
        self.assertEqual(graph.bfs, ['a', 'b', 'c', 'd'])
        self.assertEqual(graph.edges['b'], ['d'])
