from dataclasses import dataclass
import re

from .config import NAME_PATTERN
from .errors import AppError
from .markers import marker_applies
from .versions import parse_specifiers

REQUIREMENT_RE = re.compile(
    rf"\s*({NAME_PATTERN})\s*(?:\[([^\]]*)\])?\s*(.*)",
)


def normalize(name):
    return re.sub(r'[-_.]+', '-', name).lower()


@dataclass(frozen=True)
class Requirement:
    name: str
    specifier: str = ''
    extras: frozenset = frozenset()
    marker: str = ''

    def applies(self, extras=()):
        return marker_applies(self.marker, extras)

    def __str__(self):
        extras = ''
        if self.extras:
            extras = '[' + ','.join(sorted(self.extras)) + ']'
        text = self.name + extras + self.specifier
        if self.marker:
            text += '; ' + self.marker
        return text


def parse_requirement(text):
    if not isinstance(text, str):
        raise AppError("Зависимость должна быть строкой.")
    declaration, separator, marker = text.partition(';')
    match = REQUIREMENT_RE.fullmatch(declaration)
    if match is None:
        raise AppError(f"Неверная зависимость: {text}")
    name, extras_text, specifier = match.groups()
    specifier = specifier.strip()
    if specifier.startswith('@'):
        raise AppError(f"Прямые URL зависимостей не поддерживаются: {name}")
    parse_specifiers(specifier)
    extras = []
    for extra in (extras_text or '').split(','):
        if not extra.strip():
            continue
        if re.fullmatch(NAME_PATTERN, extra.strip()) is None:
            raise AppError(f"Неверное имя extra: {extra}")
        extras.append(normalize(extra.strip()))
    if separator and not marker.strip():
        raise AppError(f"Пустой маркер зависимости: {text}")
    return Requirement(normalize(name), specifier, frozenset(extras),
                       marker.strip())
