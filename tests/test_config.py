from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.cli import main
from src.config import parse_config

ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def parse(self, *extra):
        return parse_config(['--package', 'requests', '--version', '2.32.3',
                             *extra])

    def test_all_settings(self):
        config = self.parse('--ascii-tree', '--stage', '1')
        self.assertTrue(config.ascii_tree)
        self.assertFalse(config.test)
        self.assertEqual(config.stage, 1)
        self.assertIn('repository=https://pypi.org', config.describe())
        self.assertIn('version=2.32.3', config.describe())

    def test_invalid_parameters(self):
        cases = [('--package', '../x'), ('--version', 'bad version'),
                 ('--repository', 'ftp://host'), ('--stage', '6'),
                 ('--repository', 'https://host:bad'),
                 ('--repository', 'https://user:pass@host'),
                 ('--test', 'true'), ('--ascii-tree', 'yes'),
                 ('--test', '--repository', '/missing/graph.json')]
        for args in cases:
            with self.subTest(args=args), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    self.parse(*args)
                self.assertEqual(error.exception.code, 2)

    def test_missing_arguments(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_config([])

    def test_test_repository(self):
        config = parse_config([
            '--package', 'A', '--version', '1.0', '--test',
            '--repository', str(ROOT / 'examples/diamond.json'),
        ])
        self.assertTrue(config.test)

    def test_stage1_output(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(['--package', 'requests', '--version', '2.32.3',
                         '--stage', '1'])
        self.assertEqual(code, 0)
        self.assertIn('ascii_tree=false', output.getvalue())

    def test_launch_from_other_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([
                sys.executable, '-B', str(ROOT / 'src/__main__.py'),
                '--stage', '1', '--package', 'requests',
                '--version', '2.32.3',
            ], cwd=directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('package=requests', result.stdout)
