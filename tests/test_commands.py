import base64
import unittest

from src.commands import Shell
from src.shell import CommandError
from src.vfs import Node, VirtualFS


def sample_fs():
    fs = VirtualFS()
    for name in ['/docs', '/docs/deep', '/docs/deep/level3',
                 '/docs/empty', '/Мои документы']:
        fs.nodes[name] = Node(directory=True)
    lines = ''.join(f'line {number}\n' for number in range(1, 16))
    fs.nodes['/docs/lines.txt'] = Node(
        False, base64.b64encode(lines.encode()).decode(),
    )
    fs.nodes['/.hidden'] = Node(False)
    fs.nodes['/binary.bin'] = Node(False, base64.b64encode(b'\xff').decode())
    return fs


class CommandsTests(unittest.TestCase):

    def setUp(self):
        self.shell = Shell(sample_fs())

    def run_command(self, command):
        return self.shell.execute(command).output

    def test_ls_hidden_and_directories(self):
        self.assertIn('docs/', self.run_command('ls'))
        self.assertNotIn('.hidden', self.run_command('ls'))
        self.assertIn('.hidden', self.run_command('ls -a'))
        self.assertEqual(self.run_command('ls docs/lines.txt'), 'lines.txt')

    def test_multiple_ls_paths(self):
        output = self.run_command('ls docs "Мои документы"')
        self.assertIn('docs:\n', output)
        self.assertIn('Мои документы:\n', output)

    def test_cd_paths(self):
        self.run_command('cd "Мои документы"')
        self.run_command('cd ../docs/deep/./level3')
        self.assertEqual(self.shell.cwd, '/docs/deep/level3')
        self.run_command('cd ../../..')
        self.assertEqual(self.shell.cwd, '/')
        self.run_command('cd docs')
        self.run_command('cd')
        self.assertEqual(self.shell.cwd, '/')
        self.assertEqual(self.run_command('ls docs/empty'), '')

    def test_cd_errors_preserve_cwd(self):
        for command in ['cd absent', 'cd docs/lines.txt', 'cd one two']:
            with self.subTest(command=command):
                with self.assertRaises(CommandError):
                    self.run_command(command)
                self.assertEqual(self.shell.cwd, '/')

    def test_tail_default(self):
        expected = [f'line {number}' for number in range(6, 16)]
        self.assertEqual(
            self.run_command('tail docs/lines.txt').splitlines(), expected,
        )

    def test_tail_count_modes(self):
        for option in ['-n3', '-n 3', '-n -3', '-n +13']:
            with self.subTest(option=option):
                self.assertEqual(
                    self.run_command(f'tail {option} docs/lines.txt'),
                    'line 13\nline 14\nline 15',
                )
        self.assertEqual(self.run_command('tail -n 0 docs/lines.txt'), '')
        self.assertEqual(
            len(self.run_command('tail -n 100 docs/lines.txt').splitlines()),
            15,
        )

    def test_tail_multiple_files(self):
        output = self.run_command('tail docs/lines.txt docs/lines.txt')
        self.assertEqual(output.count('==> docs/lines.txt <=='), 2)

    def test_tail_errors(self):
        commands = ['tail', 'tail -n', 'tail -n abc docs/lines.txt',
                    'tail -f docs/lines.txt', 'tail missing', 'tail docs',
                    'tail binary.bin']
        for command in commands:
            with self.subTest(command=command):
                with self.assertRaises(CommandError):
                    self.run_command(command)

    def test_tail_rejects_invalid_count_formats(self):
        for count in ['1_0', ' 3 ', '3.0', '1e2', '', '++3']:
            with self.subTest(count=count):
                with self.assertRaises(CommandError):
                    self.run_command(f'tail -n "{count}" docs/lines.txt')

    def test_tail_preserves_characters_inside_lines(self):
        text = 'first\vpart\nlast\u2028part\n'
        self.shell.fs.nodes['/text.txt'] = Node(
            False, base64.b64encode(text.encode()).decode(),
        )
        self.assertEqual(self.run_command('tail -n 1 text.txt'),
                         'last\u2028part')
        self.assertEqual(self.run_command('tail -n +2 text.txt'),
                         'last\u2028part')

    def test_tail_empty_file_and_missing_final_newline(self):
        self.shell.fs.nodes['/empty.txt'] = Node(False)
        self.shell.fs.nodes['/text.txt'] = Node(
            False, base64.b64encode(b'first\nlast').decode(),
        )
        self.assertEqual(self.run_command('tail empty.txt'), '')
        self.assertEqual(self.run_command('tail -n +2 empty.txt'), '')
        self.assertEqual(self.run_command('tail -n 1 text.txt'), 'last')

    def test_cal_month_and_year(self):
        february = self.run_command('cal 2 2024')
        self.assertIn('29', february)
        self.assertNotIn('30', february)
        year = self.run_command('cal 2026')
        self.assertIn('January', year)
        self.assertIn('December', year)
        self.assertTrue(self.run_command('cal'))

    def test_cal_errors(self):
        for command in ['cal 0 2026', 'cal 13 2026', 'cal 0',
                        'cal 10000', 'cal text', 'cal 1 2 3']:
            with self.subTest(command=command):
                with self.assertRaises(CommandError):
                    self.run_command(command)

    def test_errors_then_valid_command(self):
        for command in ['unknown', 'ls -z', 'ls ""', 'exit now']:
            with self.subTest(command=command):
                with self.assertRaises(CommandError):
                    self.run_command(command)
        self.assertIn('lines.txt', self.run_command('ls docs'))
        self.assertTrue(self.shell.execute('exit').should_exit)
        self.assertEqual(self.run_command(''), '')

    def test_double_dash_operand(self):
        self.shell.fs.nodes['/-file'] = Node(False)
        self.assertEqual(self.run_command('ls -- -file'), '-file')


if __name__ == '__main__':
    unittest.main()
