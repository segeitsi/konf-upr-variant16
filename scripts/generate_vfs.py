"""Создание тестовых ZIP; архивы не хранятся в Git."""

from pathlib import Path
import sys
import zipfile


def generate(directory: Path) -> None:
    """Создать минимальный, обычный и вложенный наборы VFS."""
    directory.mkdir(parents=True, exist_ok=True)
    samples = {
        "minimal.zip": {},
        "files.zip": {"hello.txt": b"Hello\n", "second.txt": b"Second\n"},
        "nested.zip": {
            "docs/lines.txt": "".join(
                f"line {number}\n" for number in range(1, 16)
            ).encode(),
            "docs/deep/level3/note.txt": "Вложенный файл\n".encode(),
            "docs/empty/": b"", "Мои документы/": b"",
            "binary.bin": bytes([0, 255, 128]),
            ".hidden": b"hidden\n",
        },
    }
    samples["Моя VFS.zip"] = samples["nested.zip"]
    for name, entries in samples.items():
        with zipfile.ZipFile(directory / name, "w") as archive:
            for path, content in entries.items():
                archive.writestr(path, content)
    (directory / "invalid.zip").write_text("This is not a ZIP")


if __name__ == "__main__":
    generate(Path(sys.argv[1] if len(sys.argv) > 1 else "data"))
