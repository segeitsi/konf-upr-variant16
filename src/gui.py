"""Графический REPL для первого этапа практической работы."""

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .shell import CommandError, execute_command

VFS_NAME = "MyVFS"


class ShellWindow:
    """Окно с историей диалога и полем ввода команд."""

    def __init__(self, root: tk.Tk) -> None:
        """Создать интерфейс и привязать Enter к выполнению команды."""
        self.root = root
        root.title(f"Эмулятор оболочки — {VFS_NAME}")
        root.geometry("820x520")
        root.minsize(540, 320)
        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        self._create_output(frame)
        self._create_input(frame)
        self.write(
            "Эмулятор оболочки · вариант 16 · этап 1\n"
            "Команды: ls [пути…], cd [путь], exit.\n"
            "ls и cd пока показывают только имя и аргументы.\n"
            'Путь с пробелами: cd "Мои документы"\n'
        )
        self.entry.focus_set()

    def _create_output(self, parent: ttk.Frame) -> None:
        """Создать область вывода с прокруткой и цветом для ошибок."""
        self.output = ScrolledText(
            parent, wrap="word", state="disabled",
            font="TkFixedFont", background="#18212b",
            foreground="#e7edf3", padx=12, pady=12,
        )
        self.output.pack(fill="both", expand=True, pady=(0, 12))
        self.output.tag_configure("prompt", foreground="#82d9b0")
        self.output.tag_configure("error", foreground="#ff9c9c")

    def _create_input(self, parent: ttk.Frame) -> None:
        """Создать поле ввода, приглашение и кнопку выполнения."""
        row = ttk.Frame(parent)
        row.pack(fill="x")
        ttk.Label(row, text=f"{VFS_NAME}:/$").pack(side="left")
        self.entry = ttk.Entry(row, font="TkFixedFont")
        self.entry.pack(side="left", fill="x", expand=True, padx=8)
        self.entry.bind("<Return>", self.submit)
        ttk.Button(
            row, text="Выполнить", command=self.submit,
        ).pack(side="right")

    def write(self, text: str, tag: str = "") -> None:
        """Добавить текст в историю и прокрутить её до конца."""
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n", tag)
        self.output.configure(state="disabled")
        self.output.see("end")

    def submit(self, event: tk.Event | None = None) -> str:
        """Обработать ввод; ошибка не прерывает следующий ввод."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        if not line.strip():
            return "break"
        self.write(f"{VFS_NAME}:/$ {line}", "prompt")
        try:
            result = execute_command(line)
        except CommandError as error:
            self.write(f"Ошибка: {error}", "error")
        else:
            if result.output:
                self.write(result.output)
            if result.should_exit:
                self.root.destroy()
                return "break"
        self.entry.focus_set()
        return "break"


def main() -> None:
    """Запустить графический цикл обработки команд."""
    root = tk.Tk()
    ShellWindow(root)
    root.mainloop()
