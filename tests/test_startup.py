import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src.config import Config, parse_config
from src.startup import run_startup
from src.commands import Shell
from src.vfs import VirtualFS, Node


class ConfigTests(unittest.TestCase):

    def test_defaults(self):
        config = parse_config([])
        self.assertEqual(config.vfs_name, "MyVFS")
        self.assertIsNone(config.startup_path)
        self.assertIn("VFS: не задана", config.describe())
        self.assertIn("Стартовый скрипт: не задан", config.describe())

    def test_paths_with_spaces(self):
        config = parse_config([
            "--vfs", "data/Моя VFS.zip",
            "--startup", "scripts/мой скрипт.txt",
        ])
        self.assertEqual(config.vfs_name, "Моя VFS.zip")
        self.assertEqual(config.startup_path, Path("scripts/мой скрипт.txt"))
        self.assertIn("data/Моя VFS.zip", config.describe())
        self.assertIn("scripts/мой скрипт.txt", config.describe())

    def test_each_parameter_is_optional(self):
        self.assertEqual(
            parse_config(["--vfs", "demo.zip"]), Config(Path("demo.zip"))
        )
        self.assertEqual(
            parse_config(["--startup", "demo.txt"]),
            Config(startup_path=Path("demo.txt")),
        )

    def test_cli_errors(self):
        for arguments in [["--unknown"], ["--vfs"], ["--startup"]]:
            with self.subTest(arguments=arguments):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        parse_config(arguments)
                self.assertEqual(raised.exception.code, 2)


class StartupTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "мой скрипт.txt"
        self.output = []
        fs = VirtualFS()
        fs.nodes["/Мои документы"] = Node(directory=True)
        self.shell = Shell(fs)

    def write(self, text, tag):
        self.output.append((text, tag))

    def run_text(self, text):
        self.path.write_text(text, encoding="utf-8")
        return run_startup(self.path, self.write,
                           lambda: f"demo.zip:{self.shell.cwd}$",
                           execute=self.shell.execute)

    def test_successful_dialogue(self):
        result = self.run_text('ls\ncd "Мои документы"\n')
        dialogue = [text for text, _ in self.output]
        self.assertEqual(dialogue[1], "demo.zip:/$ ls")
        self.assertEqual(dialogue[2], "Мои документы/")
        self.assertEqual(dialogue[3], 'demo.zip:/$ cd "Мои документы"')
        self.assertEqual(self.shell.cwd, "/Мои документы")
        self.assertFalse(result.failed)
        self.assertFalse(result.should_exit)

    def test_stops_on_every_command_error(self):
        for bad_line in ['cd "bad', "abracadabra", "cd one two", "exit now"]:
            with self.subTest(command=bad_line):
                self.output.clear()
                result = self.run_text(f"ls\n{bad_line}\nls after_error\n")
                dialogue = "\n".join(text for text, _ in self.output)
                self.assertTrue(result.failed)
                self.assertFalse(result.should_exit)
                self.assertIn("строка 2", dialogue)
                self.assertIn(str(self.path), dialogue)
                self.assertNotIn("after_error", dialogue)
                self.assertEqual(self.output[-1][1], "error")

    def test_exit_stops_following_commands(self):
        result = self.run_text("ls\nexit\nabracadabra\n")
        self.assertTrue(result.should_exit)
        self.assertFalse(result.failed)
        self.assertNotIn("abracadabra", str(self.output))

    def test_empty_and_bom_scripts(self):
        result = self.run_text("\ufeff\n \nls\n")
        self.assertFalse(result.failed)
        prompts = [text for text, tag in self.output if tag == "prompt"]
        self.assertEqual(prompts, ["demo.zip:/$ ls"])
        self.output.clear()
        self.assertFalse(self.run_text("").failed)

    def test_actual_line_numbers(self):
        result = self.run_text("\nls\n\nunknown\n")
        self.assertTrue(result.failed)
        self.assertIn("строка 4", self.output[-1][0])

    def test_file_errors(self):
        paths = [self.path, Path(self.directory.name)]
        for path in paths:
            with self.subTest(path=path):
                result = run_startup(path, self.write, "demo:/$")
                self.assertTrue(result.failed)
                self.assertEqual(self.output[-1][1], "error")
        self.path.write_bytes(b"\xff\xfe")
        self.assertTrue(run_startup(self.path, self.write, "demo:/$").failed)


if __name__ == "__main__":
    unittest.main()
