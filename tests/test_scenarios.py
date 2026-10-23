from pathlib import Path
from datetime import datetime
import tempfile
import unittest
from unittest.mock import patch

from scripts.generate_vfs import generate
from src.commands import Shell
from src.startup import run_startup
from src.vfs import VirtualFS

SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'


class ScenarioTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        generate(self.root)

    def run_script(self, script, archive='nested.zip'):
        self.shell = Shell(VirtualFS.load(self.root / archive))
        self.dialogue = []
        return run_startup(
            SCRIPTS / script,
            lambda text, tag: self.dialogue.append((text, tag)),
            lambda: f'demo:{self.shell.cwd}$',
            execute=self.shell.execute,
        )

    def test_stage3_structures(self):
        for archive in ['minimal.zip', 'files.zip', 'nested.zip']:
            with self.subTest(archive=archive):
                result = self.run_script('stage3.txt', archive)
                self.assertFalse(result.failed)
                self.assertTrue(result.should_exit)

    def test_stage4_dialogue(self):
        result = self.run_script('stage4.txt')
        self.assertFalse(result.failed)
        self.assertFalse(result.should_exit)
        self.assertEqual(self.shell.cwd, '/')
        self.assertIn(('demo:/docs/deep/level3$ ls', 'prompt'),
                      self.dialogue)
        self.assertIn(('demo:/Мои документы$ ls', 'prompt'), self.dialogue)
        self.assertIn(('line 13\nline 14\nline 15', ''), self.dialogue)

    def test_stage4_errors_stop_script(self):
        for name in ['ls', 'cd', 'tail', 'cal']:
            with self.subTest(command=name):
                self.assertTrue(self.run_script(f'error_{name}.txt').failed)
                transcript = '\n'.join(text for text, _ in self.dialogue)
                self.assertIn('строка 2', transcript)
                self.assertNotIn('not-executed-after-error', transcript)
                self.assertTrue(self.shell.execute('ls docs').output)

    def test_stage5_mutations(self):
        before = (self.root / 'nested.zip').read_bytes()
        self.assertFalse(self.run_script('stage5.txt').failed)
        for path in ['/new.txt', '/файл с пробелами.txt', '/-file',
                     '/docs/deep/level3/local.txt']:
            self.assertEqual(self.shell.fs.get(path).data(), b'')
        self.assertNotIn('/docs/empty', self.shell.fs.nodes)
        self.assertNotIn('/Мои документы', self.shell.fs.nodes)
        self.assertEqual((self.root / 'nested.zip').read_bytes(), before)
        self.assertEqual(self.shell.fs.get('/binary.bin').data(),
                         bytes([0, 255, 128]))

    def test_stage5_errors_stop_script(self):
        for name in ['touch', 'rmdir', 'rmdir_missing', 'rmdir_file',
                     'rmdir_root', 'rmdir_current']:
            with self.subTest(mode=name):
                self.assertTrue(self.run_script(f'error_{name}.txt').failed)
                transcript = '\n'.join(text for text, _ in self.dialogue)
                self.assertNotIn('not-executed-after-error', transcript)
                self.assertIn('/docs/empty', self.shell.fs.nodes)
                self.shell.execute('touch /after-error')
                self.assertIn('/after-error', self.shell.fs.nodes)

    def test_final_success_script(self):
        result = self.run_script('success.txt')
        self.assertFalse(result.failed)
        self.assertFalse(result.should_exit)
        self.assertEqual(self.shell.cwd, '/')
        self.assertIn('/new.txt', self.shell.fs.nodes)

    def test_stage5_dialogue_shows_changes(self):
        shell = Shell(VirtualFS.load(self.root / 'nested.zip'))
        dialogue = []
        with patch('src.vfs.datetime') as clock:
            clock.now.return_value = datetime(2027, 1, 2, 3, 4, 5, 123456)
            result = run_startup(
                SCRIPTS / 'stage5.txt',
                lambda text, tag: dialogue.append(text), 'demo:/$',
                execute=shell.execute,
            )
        self.assertFalse(result.failed)
        listings = [text for text in dialogue
                    if '\n' not in text and text.endswith(' lines.txt')]
        self.assertEqual(len(listings), 2)
        self.assertNotEqual(listings[0], listings[1])
        self.assertIn('2027-01-02 03:04:05.123456', listings[1])
        self.assertEqual(listings[0].split()[:2], listings[1].split()[:2])
        positions = [index for index, text in enumerate(dialogue)
                     if text == 'demo:/$ ls -l docs']
        self.assertEqual(len(positions), 2)
        self.assertIn('empty/', dialogue[positions[0] + 1])
        self.assertNotIn('empty/', dialogue[positions[1] + 1])


if __name__ == '__main__':
    unittest.main()
