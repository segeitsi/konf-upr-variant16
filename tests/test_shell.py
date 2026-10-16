import unittest

from src.shell import CommandError, execute_command, parse_command


class ParserTests(unittest.TestCase):

    def test_quotes_and_spaces(self):
        for quote in ('"', "'"):
            with self.subTest(quote=quote):
                line = f"  cd   {quote}Мои документы{quote}  "
                self.assertEqual(
                    parse_command(line), ["cd", "Мои документы"]
                )

    def test_multiple_and_empty_arguments(self):
        self.assertEqual(
            parse_command('ls "" "a b" c'), ["ls", "", "a b", "c"]
        )

    def test_escaped_quotes(self):
        self.assertEqual(
            parse_command(r'ls "a\"b"'), ["ls", 'a"b']
        )

    def test_hash_is_not_a_comment(self):
        self.assertEqual(parse_command("ls #notes"), ["ls", "#notes"])

    def test_invalid_syntax(self):
        for line in ['cd "abc', "cd 'abc", "ls abc\\"]:
            with self.subTest(line=line):
                with self.assertRaises(CommandError):
                    parse_command(line)


if __name__ == "__main__":
    unittest.main()
