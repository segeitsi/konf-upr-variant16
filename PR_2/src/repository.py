import json
import platform
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .errors import AppError
from .requirements import parse_requirement
from .versions import matches, parse_specifiers, Version

TIMEOUT = 15
MAX_RESPONSE_BYTES = 16 * 1024 * 1024


class PyPIRepository:
    def __init__(self, url):
        self.url = url.rstrip('/')
        self.cache = {}

    def _get(self, path):
        if path in self.cache:
            return self.cache[path]
        request = Request(self.url + path, headers={
            'Accept': 'application/json', 'User-Agent': 'mirea-pr2/1.0',
        })
        try:
            with urlopen(request, timeout=TIMEOUT) as response:
                data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise AppError("Ответ репозитория слишком большой.")
            result = json.loads(data)
        except HTTPError as error:
            raise AppError(f"Репозиторий ответил HTTP {error.code}: {path}")
        except (OSError, URLError, ValueError) as error:
            raise AppError(f"Не удалось прочитать репозиторий: {error}")
        if not isinstance(result, dict):
            raise AppError("Репозиторий вернул JSON неверной структуры.")
        self.cache[path] = result
        return result

    def metadata(self, name, version):
        path = f'/pypi/{quote(name, safe="")}/{quote(version, safe="")}/json'
        info = self._get(path).get('info')
        if not isinstance(info, dict):
            raise AppError(f"Нет метаданных для {name}=={version}")
        required_python = info.get('requires_python') or ''
        if not matches(platform.python_version(), required_python):
            raise AppError(f"{name}=={version}: нужен Python {required_python}")
        if 'requires_dist' in (info.get('dynamic') or []):
            raise AppError(f"{name}: зависимости динамические, данных нет.")
        return info

    def dependencies(self, name, version, extras=()):
        info = self.metadata(name, version)
        raw = info.get('requires_dist') or []
        if not isinstance(raw, list):
            raise AppError(f"Неверный список зависимостей: {name}")
        result = []
        for declaration in raw:
            requirement = parse_requirement(declaration)
            if requirement.applies(extras):
                result.append(requirement)
        return result

    def resolve(self, requirement):
        project = self._get(f'/pypi/{quote(requirement.name, safe="")}/json')
        releases = project.get('releases')
        if not isinstance(releases, dict):
            raise AppError(f"Нет версий пакета {requirement.name}")
        candidates = self._candidates(releases, requirement.specifier)
        for version in sorted(candidates, key=Version, reverse=True):
            files = releases[version]
            if any(self._usable_file(item) for item in files):
                return version
        raise AppError(f"Нет подходящей версии: {requirement}")

    def _candidates(self, releases, specifier):
        candidates = []
        allow_pre = any(Version(text.removesuffix('.*')).prerelease
                        for _, text in parse_specifiers(specifier))
        for text in releases:
            try:
                version = Version(text)
            except AppError:
                continue
            if version.prerelease and not allow_pre:
                continue
            if matches(text, specifier):
                candidates.append(text)
        return candidates

    def _usable_file(self, item):
        if not isinstance(item, dict) or item.get('yanked'):
            return False
        required = item.get('requires_python') or ''
        return matches(platform.python_version(), required)
