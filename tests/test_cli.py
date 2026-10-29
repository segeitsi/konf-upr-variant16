from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import unittest

from src.cli import main

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_stage(self, stage, graph='diamond', extra=()):
        output, errors = io.StringIO(), io.StringIO()
        arguments = ['--stage', str(stage), '--test', '--package', 'A',
                     '--version', '1.0', '--repository',
                     str(ROOT / f'examples/{graph}.json'), *extra]
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(arguments)
        return code, output.getvalue(), errors.getvalue()

    def test_all_five_stages(self):
        expected = {1: 'package=A', 2: 'Прямые зависимости', 3: 'BFS:',
                    4: 'Порядок загрузки:', 5: 'direction: right'}
        for stage, text in expected.items():
            code, output, errors = self.run_stage(stage)
            self.assertEqual(code, 0, errors)
            self.assertIn(text, output)

    def test_ascii_only_when_requested(self):
        self.assertNotIn('ASCII:', self.run_stage(5)[1])
        output = self.run_stage(5, extra=['--ascii-tree'])[1]
        self.assertIn('ASCII:', output)
        self.assertIn('[already shown]', output)

    def test_cycle_error_and_visualization(self):
        code, output, errors = self.run_stage(4, 'cycle')
        self.assertEqual(code, 1)
        self.assertEqual(output, '')
        self.assertIn('цикл', errors)
        code, output, errors = self.run_stage(5, 'cycle', ['--ascii-tree'])
        self.assertEqual(code, 0, errors)
        self.assertIn('[cycle]', output)
