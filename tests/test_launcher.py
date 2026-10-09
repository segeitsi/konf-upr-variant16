"""Проверки реального скрипта запуска без открытия GUI."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipIf(os.name == "nt", "run.sh предназначен для macOS/Linux")
class LauncherTests(unittest.TestCase):
    """Проверить передачу аргументов и запуск из другого каталога."""

    def run_launcher(self, *arguments):
        """Вызвать run.sh из временной рабочей директории."""
        launcher = Path(__file__).resolve().parents[1] / "run.sh"
        environment = os.environ.copy()
        environment["PYTHON"] = sys.executable
        with tempfile.TemporaryDirectory() as directory:
            return subprocess.run(
                ["sh", str(launcher), *arguments], cwd=directory,
                env=environment, capture_output=True, text=True,
            )

    def test_help(self):
        """run.sh передаёт --help и находит исходники из любого каталога."""
        result = self.run_launcher("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--vfs", result.stdout)
        self.assertIn("--startup", result.stdout)

    def test_invalid_parameter(self):
        """Ошибочный параметр не теряется и возвращает ненулевой код."""
        result = self.run_launcher("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--unknown", result.stderr)


class DirectLauncherTests(unittest.TestCase):
    """Проверить прямой запуск файла, как через кнопку в редакторе."""

    def run_entry(self, *arguments):
        """Запустить точку входа из другой рабочей директории."""
        entry = Path(__file__).resolve().parents[1] / "src" / "__main__.py"
        with tempfile.TemporaryDirectory() as directory:
            return subprocess.run(
                [sys.executable, "-B", str(entry), *arguments],
                cwd=directory, capture_output=True, text=True,
            )

    def test_help(self):
        """Прямой запуск файла находит пакет и показывает справку."""
        result = self.run_entry("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--startup", result.stdout)

    def test_invalid_parameter(self):
        """При прямом запуске ошибка аргумента обрабатывается парсером."""
        result = self.run_entry("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("ImportError", result.stderr)


if __name__ == "__main__":
    unittest.main()
