from pathlib import Path
import tempfile
import unittest
import zipfile

from src.vfs import VirtualFS, VFSError


class VFSTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.zip"

    def archive(self, entries):
        with zipfile.ZipFile(self.path, "w") as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        return VirtualFS.load(self.path)

    def test_empty(self):
        self.assertEqual(self.archive({}).children("/"), [])

    def test_nested_and_binary(self):
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
        fs = self.archive({"dir/file.txt": b"hello"})
        before = self.path.read_bytes()
        self.assertEqual(fs.text("/dir/file.txt"), "hello")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.path])

    def test_missing_and_corrupt_archive(self):
        with self.assertRaises(VFSError):
            VirtualFS.load(self.path)
        self.path.write_text("not a zip")
        with self.assertRaises(VFSError):
            VirtualFS.load(self.path)

    def test_invalid_zip_paths(self):
        for name in ["../outside", "/absolute", "a/../../bad", "a\\b"]:
            with self.subTest(name=name):
                with self.assertRaises(VFSError):
                    self.archive({name: b"x"})
        with self.assertRaises(VFSError):
            self.archive({"a": b"file", "a/b.txt": b"child"})

    def test_invalid_operations(self):
        fs = self.archive({"binary": b"\xff", "dir/": b""})
        for callback in [lambda: fs.get("/absent"),
                         lambda: fs.children("/binary"),
                         lambda: fs.text("/dir"),
                         lambda: fs.text("/binary"),
                         lambda: fs.resolve("")]:
            with self.assertRaises(VFSError):
                callback()

    def test_symlink_entry_is_rejected(self):
        entry = zipfile.ZipInfo("shortcut")
        entry.create_system = 3
        entry.external_attr = 0xA1FF0000
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr(entry, "outside.txt")
        with self.assertRaisesRegex(VFSError, "Символические ссылки"):
            VirtualFS.load(self.path)

    def test_regular_unix_file_is_loaded(self):
        entry = zipfile.ZipInfo("regular.txt")
        entry.create_system = 3
        entry.external_attr = 0x81A40000
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr(entry, b"text")
        self.assertEqual(VirtualFS.load(self.path).text("/regular.txt"),
                         "text")

    def test_explicit_directories_after_implicit_parents(self):
        fs = self.archive({"a/b/file.txt": b"text", "a/": b"", "a/b/": b""})
        self.assertEqual(fs.children("/a"), ["b"])
        self.assertEqual(fs.text("/a/b/file.txt"), "text")

    def test_conflicting_normalized_entries_are_rejected(self):
        for entries in [{"a//file.txt": b"first", "a/file.txt": b"second"},
                        {"a/file.txt": b"text", "a": b"file"}]:
            with self.subTest(entries=entries):
                with self.assertRaisesRegex(VFSError, "Повторяющийся путь"):
                    self.archive(entries)


if __name__ == "__main__":
    unittest.main()
