import io
import json
from urllib.error import HTTPError, URLError
import unittest
from unittest.mock import patch

from src.errors import AppError
from src.repository import PyPIRepository


class HttpTests(unittest.TestCase):
    def test_metadata_cache_prevents_repeated_requests(self):
        response = io.BytesIO(json.dumps({'info': {'requires_dist': []}})
                              .encode())
        repo = PyPIRepository('https://example.org')
        with patch('src.repository.urlopen', return_value=response) as get:
            self.assertEqual(repo.dependencies('demo', '1.0'), [])
            self.assertEqual(repo.dependencies('demo', '1.0'), [])
        self.assertEqual(get.call_count, 1)

    def test_network_http_and_json_errors(self):
        errors = [URLError('offline'), TimeoutError('timeout'),
                  HTTPError('https://example.org', 404, 'missing', {}, None)]
        repo = PyPIRepository('https://example.org')
        for error in errors:
            with self.subTest(error=error):
                with patch('src.repository.urlopen', side_effect=error):
                    with self.assertRaises(AppError):
                        repo.dependencies('demo', '1.0')
        for data in [b'not json', b'[]', b'{"info": null}']:
            with patch('src.repository.urlopen', return_value=io.BytesIO(data)):
                with self.assertRaises(AppError):
                    repo.dependencies('demo', '1.0')

    def test_python_incompatibility(self):
        repo = PyPIRepository('https://example.org')
        payload = {'info': {'requires_python': '<2'}}
        with patch.object(repo, '_get', return_value=payload):
            with self.assertRaisesRegex(AppError, 'нужен Python'):
                repo.dependencies('demo', '1.0')
