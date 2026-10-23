import base64
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from src.commands import Shell
from src.shell import CommandError
from src.vfs import Node, VirtualFS


class LongListingTests(unittest.TestCase):
    def setUp(self):
        self.fs = VirtualFS()
        self.fs.nodes['/docs'] = Node(directory=True)
        self.fs.nodes['/docs/empty'] = Node(directory=True)
        self.fs.nodes['/.hidden'] = Node(directory=False)
        self.fs.nodes['/binary.bin'] = Node(
            False, base64.b64encode(bytes([0, 255, 128])).decode(),
        )
        self.fs.nodes['/message.txt'] = Node(
            directory=False,
            content=base64.b64encode('Привет\n'.encode()).decode(),
            modified=datetime(2020, 1, 2, 3, 4, 6),
            mode=0o100640,
        )
        self.shell = Shell(self.fs)

    def run_command(self, command):
        return self.shell.execute(command).output

    def test_file_permissions_size_and_time(self):
        fields = self.run_command('ls -l message.txt').split(maxsplit=4)
        self.assertEqual(fields, ['-rw-r-----', '13', '2020-01-02',
                                  '03:04:06.000000', 'message.txt'])
        fields = self.run_command('ls -l binary.bin').split(maxsplit=4)
        self.assertEqual(fields[1], '3')

    def test_hidden_and_combined_flags(self):
        self.assertNotIn('.hidden', self.run_command('ls -l'))
        expected = self.run_command('ls -a -l')
        self.assertIn('.hidden', expected)
        self.assertEqual(self.run_command('ls -al'), expected)
        self.assertEqual(self.run_command('ls -la'), expected)
        self.assertIn(' .\n', expected)
        self.assertIn(' ..\n', expected)

    def test_directories_and_multiple_paths(self):
        self.assertTrue(self.run_command('ls -l docs').startswith('d'))
        self.assertIn('empty/', self.run_command('ls -l docs'))
        output = self.run_command('ls -l message.txt docs')
        self.assertIn('message.txt:\n-rw-r-----', output)
        self.assertIn('docs:\ndrwxr-xr-x', output)

    def test_touch_creation_is_visible(self):
        self.run_command('touch "новый файл.txt"')
        fields = self.run_command('ls -l "новый файл.txt"').split(maxsplit=4)
        self.assertEqual(fields[0], '-rw-r--r--')
        self.assertEqual(fields[1], '0')
        self.assertEqual(fields[-1], 'новый файл.txt')

    def test_touch_time_changes_but_content_is_preserved(self):
        before = self.run_command('ls -l message.txt')
        content = self.fs.get('/message.txt').data()
        changed = datetime(2026, 10, 23, 16, 1, 2, 123456)
        with patch('src.vfs.datetime') as clock:
            clock.now.return_value = changed
            self.run_command('touch message.txt')
        after = self.run_command('ls -l message.txt')
        self.assertNotEqual(before, after)
        self.assertIn('2026-10-23 16:01:02.123456', after)
        self.assertEqual(self.fs.get('/message.txt').data(), content)
        self.assertEqual(after.split(maxsplit=4)[:2], ['-rw-r-----', '13'])

    def test_rmdir_removal_is_visible(self):
        self.assertIn('empty/', self.run_command('ls -l docs'))
        self.run_command('rmdir docs/empty')
        self.assertEqual(self.run_command('ls -l docs'), '')
        with self.assertRaises(CommandError):
            self.run_command('cd docs/empty')

    def test_option_separator(self):
        self.run_command('touch -- -l')
        fields = self.run_command('ls -l -- -l').split(maxsplit=4)
        self.assertEqual(fields[-1], '-l')
        with self.assertRaises(CommandError):
            self.run_command('ls -lh')

    def test_permissions_loaded_from_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.zip'
            entry = zipfile.ZipInfo('original.txt', (2020, 1, 2, 3, 4, 6))
            entry.create_system = 3
            entry.external_attr = 0x81A00000
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr(entry, b'text')
            shell = Shell(VirtualFS.load(path))
            output = shell.execute('ls -l original.txt').output
            self.assertTrue(output.startswith('-rw-r-----'))

    def test_default_permissions_for_zip_without_unix_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.zip'
            entry = zipfile.ZipInfo('windows.txt')
            entry.create_system = 0
            entry.external_attr = 0x20
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr(entry, b'text')
            shell = Shell(VirtualFS.load(path))
            output = shell.execute('ls -l windows.txt').output
            self.assertTrue(output.startswith('-rw-r--r--'))


if __name__ == '__main__':
    unittest.main()
