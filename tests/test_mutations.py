from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from scripts.generate_vfs import generate
from src.commands import Shell
from src.shell import CommandError
from src.vfs import VirtualFS


class MutationTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        generate(self.root)
        self.path = self.root / 'nested.zip'
        self.shell = Shell(VirtualFS.load(self.path))
        self.fs = self.shell.fs

    def test_touch_empty_file_and_relative_path(self):
        self.shell.execute('cd "Мои документы"')
        self.assertEqual(self.shell.execute('touch "новый файл"').output, '')
        self.assertEqual(self.fs.get('/Мои документы/новый файл').data(), b'')
        self.assertEqual(self.shell.execute('ls').output, 'новый файл')
        self.assertEqual(self.shell.execute('tail "новый файл"').output, '')

    def test_touch_existing_nodes_preserves_content(self):
        for path in ['/docs/lines.txt', '/binary.bin', '/docs', '/']:
            with self.subTest(path=path):
                node = self.fs.get(path)
                content = node.content
                node.modified = datetime(2000, 1, 1)
                self.shell.execute(f'touch {path}')
                self.assertEqual(node.content, content)
                self.assertGreater(node.modified, datetime(2000, 1, 1))

    def test_touch_multiple_and_option_separator(self):
        self.shell.execute('touch one two "три четыре"')
        self.shell.execute('touch -- -file')
        for path in ['/one', '/two', '/три четыре', '/-file']:
            self.assertEqual(self.fs.get(path).data(), b'')

    def test_touch_errors_do_not_create_nodes(self):
        commands = ['touch', 'touch -z file', 'touch ""',
                    'touch absent/file', 'touch docs/lines.txt/child',
                    'touch missing/', 'touch docs/lines.txt/',
                    'touch "bad\x00path"']
        before = set(self.fs.nodes)
        for command in commands:
            with self.subTest(command=command):
                with self.assertRaises(CommandError):
                    self.shell.execute(command)
                self.assertEqual(set(self.fs.nodes), before)

    def test_rmdir_multiple_empty_directories(self):
        self.shell.execute('rmdir docs/empty "Мои документы"')
        self.assertNotIn('/docs/empty', self.fs.nodes)
        self.assertNotIn('/Мои документы', self.fs.nodes)
        self.assertNotIn('empty/', self.shell.execute('ls docs').output)
        with self.assertRaises(CommandError):
            self.shell.execute('cd docs/empty')

    def test_rmdir_relative_path(self):
        self.shell.execute('cd docs/deep/level3')
        self.shell.execute('rmdir ../../empty')
        self.assertNotIn('/docs/empty', self.fs.nodes)
        self.assertEqual(self.shell.cwd, '/docs/deep/level3')

    def test_rmdir_errors_preserve_nodes(self):
        before = set(self.fs.nodes)
        for command in ['rmdir', 'rmdir -p docs', 'rmdir missing',
                        'rmdir ""', 'rmdir docs/lines.txt', 'rmdir docs',
                        'rmdir /']:
            with self.subTest(command=command):
                with self.assertRaises(CommandError):
                    self.shell.execute(command)
                self.assertEqual(set(self.fs.nodes), before)

    def test_rmdir_protects_current_directory(self):
        self.shell.execute('cd docs/empty')
        for argument in ['.', '../empty', '..', '/']:
            with self.subTest(argument=argument):
                with self.assertRaises(CommandError):
                    self.shell.execute(f'rmdir {argument}')
                self.assertEqual(self.shell.cwd, '/docs/empty')
                self.assertIn('/docs/empty', self.fs.nodes)

    def test_operations_change_memory_only(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        self.shell.execute('touch /new.txt docs/lines.txt binary.bin')
        self.shell.execute('rmdir docs/empty')
        after = {path.name: path.read_bytes() for path in self.root.iterdir()}
        self.assertEqual(after, before)
        reopened = VirtualFS.load(self.path)
        self.assertNotIn('/new.txt', reopened.nodes)
        self.assertIn('/docs/empty', reopened.nodes)

    def test_new_session_discards_changes(self):
        self.shell.execute('touch scratch.txt')
        self.shell.execute('rmdir "Мои документы"')
        other = Shell(VirtualFS.load(self.path))
        self.assertNotIn('/scratch.txt', other.fs.nodes)
        self.assertIn('/Мои документы', other.fs.nodes)

    def test_multiple_operands_stop_at_first_error(self):
        with self.assertRaises(CommandError):
            self.shell.execute('touch first missing/file last')
        self.assertIn('/first', self.fs.nodes)
        self.assertNotIn('/last', self.fs.nodes)
        with self.assertRaises(CommandError):
            self.shell.execute('rmdir docs/empty absent "Мои документы"')
        self.assertNotIn('/docs/empty', self.fs.nodes)
        self.assertIn('/Мои документы', self.fs.nodes)

    def test_touch_rejects_invalid_intermediate_paths(self):
        before = {path: (node.content, node.modified)
                  for path, node in self.fs.nodes.items()}
        for path in ['missing/../new.txt', 'docs/lines.txt/../new.txt',
                     'docs/lines.txt/.', 'docs/lines.txt/..']:
            with self.subTest(path=path):
                with self.assertRaises(CommandError):
                    self.shell.execute(f'touch {path}')
                self.assertEqual(
                    {path: (node.content, node.modified)
                     for path, node in self.fs.nodes.items()},
                    before,
                )

    def test_rmdir_rejects_invalid_intermediate_paths(self):
        before = set(self.fs.nodes)
        for path in ['missing/../docs/empty', 'docs/lines.txt/../empty']:
            with self.subTest(path=path):
                with self.assertRaises(CommandError):
                    self.shell.execute(f'rmdir {path}')
                self.assertEqual(set(self.fs.nodes), before)

    def test_rmdir_rejects_dot_operand(self):
        for path in ['docs/empty/.', 'docs/empty/./']:
            with self.subTest(path=path):
                with self.assertRaises(CommandError):
                    self.shell.execute(f'rmdir {path}')
                self.assertIn('/docs/empty', self.fs.nodes)

    def test_mutations_accept_valid_parent_and_repeated_separators(self):
        self.shell.execute('cd docs/deep')
        self.shell.execute('touch ../empty//new.txt')
        self.assertEqual(self.fs.get('/docs/empty/new.txt').data(), b'')
        self.shell.execute('rmdir ../deep/../../Мои\\ документы//')
        self.assertNotIn('/Мои документы', self.fs.nodes)


if __name__ == '__main__':
    unittest.main()
