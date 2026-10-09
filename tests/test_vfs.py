"""Проверки ZIP, виртуальных путей и двоичных данных."""

from pathlib import Path
import tempfile
import unittest
import zipfile

from src.vfs import VirtualFS, VFSError


class VFSTests(unittest.TestCase):
    """Читать архив в память, сохраняя исходные данные на диске."""

    def setUp(self):
        """Создать изолированное место для ZIP."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.zip"

    def archive(self, entries):
        """Создать архив из имён и байтовых строк."""
        with zipfile.ZipFile(self.path, "w") as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        return VirtualFS.load(self.path)

    def test_empty(self):
        """Минимальный ZIP представляет пустой корень."""
        self.assertEqual(self.archive({}).children("/"), [])

    def test_nested_and_binary(self):
        """Вложенные каталоги создаются даже без отдельных записей ZIP."""
        fs = self.archive({
            "a/b/c/Мой файл.txt": "Текст\n".encode(),
            "empty/": b"", "binary.bin": bytes([0, 255, 128]),
        })
        self.assertEqual(fs.children("/"), ["a", "binary.bin", "empty"])
        self.assertEqual(fs.text("/a/b/c/Мой файл.txt"), "Текст\n")
        self.assertEqual(fs.get("/binary.bin").data(), bytes([0, 255, 128]))
        self.assertEqual(fs.get("/binary.bin").content, "AP+A")
        self.assertEqual(fs.resolve("../c/./Мой файл.txt", "/a/b/c"),
                         "/a/b/c/Мой файл.txt")
        self.assertEqual(fs.resolve("../../../..", "/a"), "/")

    def test_no_extraction(self):
        """Загрузка не меняет архив и не создаёт распакованные файлы."""
        fs = self.archive({"dir/file.txt": b"hello"})
        before = self.path.read_bytes()
        self.assertEqual(fs.text("/dir/file.txt"), "hello")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.path])

    def test_missing_and_corrupt_archive(self):
        """Отсутствующий файл и повреждённый ZIP дают понятную ошибку."""
        with self.assertRaises(VFSError):
            VirtualFS.load(self.path)
        self.path.write_text("not a zip")
        with self.assertRaises(VFSError):
            VirtualFS.load(self.path)

    def test_invalid_zip_paths(self):
        """Абсолютные пути, выход за корень и конфликт узлов запрещены."""
        for name in ["../outside", "/absolute", "a/../../bad", "a\\b"]:
            with self.subTest(name=name):
                with self.assertRaises(VFSError):
                    self.archive({name: b"x"})
        with self.assertRaises(VFSError):
            self.archive({"a": b"file", "a/b.txt": b"child"})

    def test_invalid_operations(self):
        """Ошибки типа узла и текстовой кодировки не теряются."""
        fs = self.archive({"binary": b"\xff", "dir/": b""})
        for callback in [lambda: fs.get("/absent"),
                         lambda: fs.children("/binary"),
                         lambda: fs.text("/dir"),
                         lambda: fs.text("/binary"),
                         lambda: fs.resolve("")]:
            with self.assertRaises(VFSError):
                callback()


if __name__ == "__main__":
    unittest.main()
