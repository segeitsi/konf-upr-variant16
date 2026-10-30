from pathlib import Path
import unittest

from src.errors import AppError
from src.graph import build_graph
from src.order import dependency_order
from src.test_repository import TestRepository

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


class OrderTests(unittest.TestCase):
    def graph(self, filename):
        repo = TestRepository(EXAMPLES / filename, '1.0')
        return build_graph(repo, 'A', '1.0', test=True)

    def test_chain_dependencies_first(self):
        self.assertEqual(dependency_order(self.graph('chain.json')),
                         ['C', 'B', 'A'])

    def test_diamond_shared_dependency_only_once(self):
        graph = self.graph('diamond.json')
        order = dependency_order(graph)
        self.assertEqual(order[0], 'D')
        self.assertEqual(order[-1], 'A')
        self.assertEqual(len(order), len(set(order)))
        for parent, children in graph.edges.items():
            for child in children:
                self.assertLess(order.index(child), order.index(parent))

    def test_cycle_has_no_fake_installation_order(self):
        with self.assertRaisesRegex(AppError, 'цикл'):
            dependency_order(self.graph('cycle.json'))

    def test_single_node(self):
        self.assertEqual(dependency_order(self.graph('single.json')), ['A'])
