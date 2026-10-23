import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .config import Config
from .shell import CommandError
from .commands import Shell
from .startup import run_startup
from .vfs import VirtualFS, VFSError


class ShellWindow:
    def __init__(self, root: tk.Tk, config: Config) -> None:
        self.root = root
        self.config = config
        self.shell = Shell()
        self.prompt_text = tk.StringVar(root, value=self.prompt)
        root.title(f"Эмулятор оболочки — {config.vfs_name}")
        root.geometry("820x520")
        root.minsize(540, 320)
        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        self._create_output(frame)
        self._create_input(frame)
        self.write(
            "Эмулятор оболочки · вариант 16 · этап 4\n"
            "Команды: ls [-a] [-l], cd, tail, cal, exit.\n"
            'Путь с пробелами: cd "Мои документы"\n'
        )
        self.write(config.describe())
        self.entry.focus_set()
        self.vfs = self.load_vfs()
        if self.vfs is not None:
            self.shell = Shell(self.vfs)
        if self.vfs is not None and config.startup_path is not None:
            root.after(0, self.run_startup)

    @property
    def prompt(self) -> str:
        return f"{self.config.vfs_name}:{self.shell.cwd}$"

    def load_vfs(self) -> VirtualFS | None:
        try:
            fs = VirtualFS()
            if self.config.vfs_path is not None:
                fs = VirtualFS.load(self.config.vfs_path)
        except VFSError as error:
            self.write(str(error), "error")
            self.entry.configure(state="disabled")
            return None
        self.write(f"VFS загружена: {len(fs.nodes) - 1} узлов.")
        return fs

    def _create_output(self, parent: ttk.Frame) -> None:
        self.output = ScrolledText(
            parent, wrap="word", state="disabled",
            font="TkFixedFont", background="#18212b",
            foreground="#e7edf3", padx=12, pady=12,
        )
        self.output.pack(fill="both", expand=True, pady=(0, 12))
        self.output.tag_configure("prompt", foreground="#82d9b0")
        self.output.tag_configure("error", foreground="#ff9c9c")

    def _create_input(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x")
        ttk.Label(row, textvariable=self.prompt_text).pack(side="left")
        self.entry = ttk.Entry(row, font="TkFixedFont")
        self.entry.pack(side="left", fill="x", expand=True, padx=8)
        self.entry.bind("<Return>", self.submit)
        ttk.Button(
            row, text="Выполнить", command=self.submit,
        ).pack(side="right")

    def write(self, text: str, tag: str = "") -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n", tag)
        self.output.configure(state="disabled")
        self.output.see("end")

    def submit(self, event: tk.Event | None = None) -> str:
        if self.vfs is None:
            return "break"
        line = self.entry.get()
        self.entry.delete(0, "end")
        if not line.strip():
            return "break"
        self.write(f"{self.prompt} {line}", "prompt")
        try:
            result = self.shell.execute(line)
        except CommandError as error:
            self.write(f"Ошибка: {error}", "error")
        else:
            if result.output:
                self.write(result.output)
            if result.should_exit:
                self.root.destroy()
                return "break"
        self.prompt_text.set(self.prompt)
        self.entry.focus_set()
        return "break"

    def run_startup(self) -> None:
        if self.config.startup_path is None:
            return
        result = run_startup(
            self.config.startup_path, self.write, lambda: self.prompt,
            execute=self.shell.execute,
        )
        if result.should_exit:
            self.root.destroy()
        else:
            self.prompt_text.set(self.prompt)
            self.entry.focus_set()


def main(config: Config) -> None:
    root = tk.Tk()
    ShellWindow(root, config)
    root.mainloop()
