import ast
import os
import platform
import re
import sys

from .errors import AppError
from .versions import matches, Version

TOKEN_RE = re.compile(
    r"\s*(?:('[^']*'|\"[^\"]*\")|([A-Za-z_][A-Za-z_0-9]*)"
    r"|(===|==|!=|<=|>=|~=|<|>|\(|\)))",
)
VERSION_FIELDS = {'python_version', 'python_full_version',
                  'implementation_version'}


def environment(extra=''):
    return {
        'python_version': '.'.join(platform.python_version_tuple()[:2]),
        'python_full_version': platform.python_version(),
        'implementation_version': platform.python_version(),
        'implementation_name': sys.implementation.name,
        'os_name': os.name, 'sys_platform': sys.platform,
        'platform_release': platform.release(),
        'platform_system': platform.system(),
        'platform_version': platform.version(),
        'platform_machine': platform.machine(),
        'platform_python_implementation': platform.python_implementation(),
        'extra': extra,
    }


def tokenize(text):
    tokens = []
    position = 0
    while position < len(text):
        match = TOKEN_RE.match(text, position)
        if match is None:
            raise AppError(f"Неверный маркер зависимости: {text}")
        tokens.append(next(value for value in match.groups()
                           if value is not None))
        position = match.end()
    return tokens


class MarkerParser:
    def __init__(self, text, values):
        self.tokens = tokenize(text.strip())
        self.position = 0
        self.values = values

    def parse(self):
        result = self._or()
        if self.position != len(self.tokens):
            raise AppError("Лишние элементы в маркере зависимости.")
        return result

    def _accept(self, token):
        if self.position < len(self.tokens):
            if self.tokens[self.position] == token:
                self.position += 1
                return True
        return False

    def _take(self):
        if self.position == len(self.tokens):
            raise AppError("Незавершённый маркер зависимости.")
        token = self.tokens[self.position]
        self.position += 1
        return token

    def _or(self):
        result = self._and()
        while self._accept('or'):
            right = self._and()
            result = result or right
        return result

    def _and(self):
        result = self._atom()
        while self._accept('and'):
            right = self._atom()
            result = result and right
        return result

    def _atom(self):
        if self._accept('('):
            result = self._or()
            if not self._accept(')'):
                raise AppError("Не закрыта скобка в маркере.")
            return result
        left, left_name = self._value()
        operation = self._take()
        if operation == 'not':
            if not self._accept('in'):
                raise AppError("После not в маркере требуется in.")
            operation = 'not in'
        right, right_name = self._value()
        version_field = bool({left_name, right_name} & VERSION_FIELDS)
        return compare(left, operation, right, version_field)

    def _value(self):
        token = self._take()
        if token.startswith(('"', "'")):
            return ast.literal_eval(token), None
        if token not in self.values:
            raise AppError(f"Неизвестное поле маркера: {token}")
        return self.values[token], token


def compare(left, operation, right, version_field=False):
    if operation == 'in':
        return left in right
    if operation == 'not in':
        return left not in right
    if version_field or operation in {'~=', '==='}:
        return matches(left, operation + right)
    try:
        Version(left)
        Version(right)
    except AppError:
        return _compare_text(left, operation, right)
    return matches(left, operation + right)


def _compare_text(left, operation, right):
    if operation == '==':
        return left == right
    if operation == '!=':
        return left != right
    if operation in {'>=', '<='}:
        return left == right
    if operation in {'>', '<'}:
        return False
    raise AppError(f"Неизвестная операция в маркере: {operation}")


def marker_applies(text, extras=(), values=None):
    if not text:
        return True
    base = environment() if values is None else dict(values)
    results = []
    for extra in set(extras) | {''}:
        base['extra'] = extra
        results.append(MarkerParser(text, base).parse())
    return any(results)
