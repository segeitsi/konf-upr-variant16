from pathlib import Path
import tempfile
import unittest

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


if __name__ == '__main__':
    unittest.main()
