"""Проверки кавычек, команд и восстановления после ошибок."""

import unittest

from src.shell import CommandError, execute_command, parse_command


class ParserTests(unittest.TestCase):
    """Проверить значимые случаи разбора пользовательского ввода."""

    def test_quotes_and_spaces(self):
        """Оба вида кавычек сохраняют пробелы в аргументах."""
        for quote in ('"', "'"):
            with self.subTest(quote=quote):
                line = f"  cd   {quote}Мои документы{quote}  "
                self.assertEqual(
                    parse_command(line), ["cd", "Мои документы"]
                )

    def test_multiple_and_empty_arguments(self):
        """Пустой аргумент и соседние строки не теряются."""
        self.assertEqual(
            parse_command('ls "" "a b" c'), ["ls", "", "a b", "c"]
        )

    def test_escaped_quotes(self):
        """Экранированная кавычка остаётся частью аргумента."""
        self.assertEqual(
            parse_command(r'ls "a\"b"'), ["ls", 'a"b']
        )

    def test_hash_is_not_a_comment(self):
        """На первом этапе символ решётки входит в имя файла."""
        self.assertEqual(parse_command("ls #notes"), ["ls", "#notes"])

    def test_invalid_syntax(self):
        """Незакрытые кавычки и оборванное экранирование дают ошибку."""
        for line in ['cd "abc', "cd 'abc", "ls abc\\"]:
            with self.subTest(line=line):
                with self.assertRaises(CommandError):
                    parse_command(line)


class CommandTests(unittest.TestCase):
    """Проверить контракт команд первого этапа."""

    def test_empty_input(self):
        """Пустой ввод не выводит текст и не завершает работу."""
        result = execute_command(" \t ")
        self.assertEqual(result.output, "")
        self.assertFalse(result.should_exit)

    def test_stubs(self):
        """Заглушки показывают имя и разобранные аргументы."""
        for name in ["ls", "cd"]:
            with self.subTest(name=name):
                result = execute_command(f'{name} "Мои документы"')
                self.assertEqual(
                    result.output,
                    f'Команда: {name}\nАргументы: ["Мои документы"]',
                )
                self.assertFalse(result.should_exit)

    def test_stubs_without_arguments(self):
        """Обе заглушки принимают ввод без аргументов."""
        for name in ["ls", "cd"]:
            self.assertIn("Аргументы: []", execute_command(name).output)

    def test_ls_multiple_paths(self):
        """ls сохраняет несколько аргументов."""
        self.assertIn('["a", "b"]', execute_command("ls a b").output)

    def test_unknown_command(self):
        """Неизвестная команда сообщает об ошибке."""
        with self.assertRaisesRegex(CommandError, "Неизвестная команда"):
            execute_command("abracadabra")

    def test_invalid_arguments(self):
        """cd принимает максимум один путь, exit не принимает аргументы."""
        for line in ["cd a b", "exit now"]:
            with self.subTest(line=line):
                with self.assertRaises(CommandError):
                    execute_command(line)

    def test_exit(self):
        """Команда exit запрашивает завершение приложения."""
        self.assertTrue(execute_command("exit").should_exit)

    def test_command_after_error(self):
        """Ошибка не мешает обработать следующую команду."""
        with self.assertRaises(CommandError):
            execute_command('cd "unfinished')
        self.assertEqual(execute_command("ls").output,
                         "Команда: ls\nАргументы: []")


if __name__ == "__main__":
    unittest.main()
