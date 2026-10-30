from pathlib import Path
import unittest

from src.graph import build_graph
from src.render import to_ascii, to_d2
from src.test_repository import TestRepository

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'


class RenderTests(unittest.TestCase):
    def graph(self, filename):
        repo = TestRepository(EXAMPLES / filename, '1.0')
        return build_graph(repo, 'A', '1.0', test=True)

    def test_d2_diamond_has_all_nodes_and_four_edges(self):
        output = to_d2(self.graph('diamond.json'))
        self.assertTrue(output.startswith('direction: right\n'))
        self.assertEqual(output.count(' -> '), 4)
        self.assertEqual(output.count('D==1.0'), 1)
        self.assertNotIn('Z==1.0', output)
        self.assertIn('n2 -> n3', output)

    def test_d2_cycle_preserves_closing_edge(self):
        self.assertIn('n2 -> n0', to_d2(self.graph('cycle.json')))

    def test_ascii_chain(self):
        self.assertEqual(to_ascii(self.graph('chain.json')),
                         'A==1.0\n`-- B==1.0\n    `-- C==1.0')

    def test_ascii_shared_package_and_branch_indentation(self):
        output = to_ascii(self.graph('diamond.json'))
        self.assertIn('|-- B==1.0\n|   `-- D==1.0', output)
        self.assertIn('`-- C==1.0\n    `-- D==1.0 [already shown]', output)

    def test_ascii_cycle_is_finite_and_labeled(self):
        output = to_ascii(self.graph('cycle.json'))
        self.assertIn('A==1.0 [cycle]', output)
        self.assertEqual(len(output.splitlines()), 4)

    def test_single_node_shown_in_both_formats(self):
        graph = self.graph('single.json')
        self.assertEqual(to_ascii(graph), 'A==1.0')
        self.assertIn('n0: "A==1.0"', to_d2(graph))
