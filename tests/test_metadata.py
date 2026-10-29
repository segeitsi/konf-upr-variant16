import unittest
from unittest.mock import patch

from src.errors import AppError
from src.markers import marker_applies
from src.repository import PyPIRepository
from src.requirements import parse_requirement
from src.versions import matches, Version


class VersionTests(unittest.TestCase):
    def test_order_and_normalization(self):
        versions = ['1.0.dev1', '1.0a1', '1.0b1', '1.0rc1', '1.0',
                    '1.0+abc', '1.0+1', '1.0.post1', '1.1', '1!0.1']
        self.assertEqual(sorted(versions, key=Version), versions)
        self.assertEqual(Version('v1.0.0'), Version('1'))
        self.assertEqual(Version('1.0-r2'), Version('1.0.post2'))

    def test_specifiers(self):
        cases = [('1.2.3', '>=1.0,<2', True), ('2.0', '<2', False),
                 ('1.4.9', '~=1.4.5', True), ('1.5', '~=1.4.5', False),
                 ('1.9', '~=1.4', True), ('2', '~=1.4', False),
                 ('1.2.3', '==1.2.*', True), ('1.0', '!=1.*', False),
                 ('1.0+x', '==1.0', True), ('1.0+x', '<=1.0', True),
                 ('1.0rc1', '<1.0', False), ('1.0.post1', '>1.0', False)]
        for version, specifier, expected in cases:
            with self.subTest(version=version, specifier=specifier):
                self.assertEqual(matches(version, specifier), expected)

    def test_invalid_versions_and_specifiers(self):
        for text in ['abc', '1..2', '1/', '']:
            with self.subTest(text=text), self.assertRaises(AppError):
                Version(text)
        for text in ['=>1', '~=1', '>=1.*']:
            with self.subTest(text=text), self.assertRaises(AppError):
                matches('1.2', text)


class RequirementTests(unittest.TestCase):
    def test_parse_extras_versions_and_marker(self):
        req = parse_requirement('Foo_Bar[tls,test] (>=1,<3); extra == "tls"')
        self.assertEqual(req.name, 'foo-bar')
        self.assertEqual(req.extras, {'tls', 'test'})
        self.assertFalse(req.applies())
        self.assertTrue(req.applies({'tls'}))

    def test_marker_precedence_and_versions(self):
        values = {'python_version': '3.14', 'sys_platform': 'darwin'}
        self.assertTrue(marker_applies(
            'python_version >= "3.9" and sys_platform != "win32"',
            values=values,
        ))
        self.assertTrue(marker_applies(
            '(python_version < "3.9" or sys_platform == "darwin")',
            values=values,
        ))
        self.assertFalse(marker_applies('"linux" in sys_platform',
                                       values=values))

    def test_invalid_marker_and_direct_url(self):
        for text in ['A @ https://example.org/a.whl', 'A;', '../bad']:
            with self.subTest(text=text), self.assertRaises(AppError):
                parse_requirement(text)
        for text in ['unknown == "x"', '__import__("os")',
                     'python_version >', '(extra == "x"']:
            with self.subTest(text=text), self.assertRaises(AppError):
                marker_applies(text)


class RepositoryTests(unittest.TestCase):
    def test_exact_version_endpoint_and_active_dependencies(self):
        repo = PyPIRepository('https://example.org')
        info = {'requires_dist': ['A>=1', 'B; extra == "test"',
                                 'C; python_version < "2"']}
        with patch.object(repo, '_get', return_value={'info': info}) as get:
            result = repo.dependencies('demo', '1.2')
        get.assert_called_once_with('/pypi/demo/1.2/json')
        self.assertEqual([req.name for req in result], ['a'])

    def test_latest_compatible_not_yanked_release(self):
        repo = PyPIRepository('https://example.org')
        releases = {'1.0': [{}], '2.0': [{'yanked': True}],
                    '3.0': [{'requires_python': '<2'}], '4.0rc1': [{}]}
        with patch.object(repo, '_get', return_value={'releases': releases}):
            self.assertEqual(repo.resolve(parse_requirement('demo>=1')), '1.0')

    def test_missing_and_dynamic_metadata(self):
        repo = PyPIRepository('https://example.org')
        for payload in [{}, {'info': {'dynamic': ['requires_dist']}}]:
            with patch.object(repo, '_get', return_value=payload):
                with self.assertRaises(AppError):
                    repo.dependencies('demo', '1.0')
