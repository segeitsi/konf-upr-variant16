from functools import total_ordering
import operator
import re

from .errors import AppError

VERSION_RE = re.compile(
    r"v?(?:(?P<epoch>\d+)!)?(?P<release>\d+(?:\.\d+)*)"
    r"(?:[-_.]?(?P<pre>a|b|c|rc|alpha|beta|pre|preview)"
    r"[-_.]?(?P<pre_number>\d+)?)?"
    r"(?P<post>(?:-(?P<post_dash>\d+))|(?:[-_.]?(?:post|rev|r)"
    r"[-_.]?(?P<post_number>\d+)?))?"
    r"(?P<dev>[-_.]?dev[-_.]?(?P<dev_number>\d+)?)?"
    r"(?:\+(?P<local>[a-z0-9]+(?:[-_.][a-z0-9]+)*))?",
    re.IGNORECASE,
)
PRE_ORDER = {'a': 0, 'alpha': 0, 'b': 1, 'beta': 1,
             'c': 2, 'rc': 2, 'pre': 2, 'preview': 2}
OPERATORS = {'==': operator.eq, '!=': operator.ne, '<': operator.lt,
             '<=': operator.le, '>': operator.gt, '>=': operator.ge}
SPEC_RE = re.compile(r"(===|~=|==|!=|<=|>=|<|>)\s*(\S+)")
MIN_COMPATIBLE_PARTS = 2
INFINITY = float('inf')
NO_POST = -1


@total_ordering
class Version:
    def __init__(self, text):
        match = VERSION_RE.fullmatch(text)
        if match is None:
            raise AppError(f"Неверная версия: {text}")
        fields = match.groupdict()
        self.text = text
        self.epoch = int(fields['epoch'] or 0)
        self.release = tuple(map(int, fields['release'].split('.')))
        self.pre = fields['pre']
        self.dev = fields['dev'] is not None
        self.post = self._post(fields)
        self.local = fields['local']
        self.key = self._key(fields)

    def _post(self, fields):
        if fields['post'] is None:
            return NO_POST
        return int(fields['post_dash'] or fields['post_number'] or 0)

    def _key(self, fields):
        release = list(self.release)
        while release and not release[-1]:
            release.pop()
        pre = (3, 0)
        if self.dev and self.post == NO_POST:
            pre = (-1, 0)
        if self.pre:
            pre = (PRE_ORDER[self.pre.lower()],
                   int(fields['pre_number'] or 0))
        dev = INFINITY
        if self.dev:
            dev = int(fields['dev_number'] or 0)
        local = ()
        if self.local:
            local = tuple(self._local_part(part) for part in
                          re.split(r'[-_.]', self.local.lower()))
        return self.epoch, tuple(release), pre, self.post, dev, local

    def _local_part(self, part):
        if part.isdigit():
            return 1, int(part)
        return 0, part

    @property
    def prerelease(self):
        return bool(self.pre or self.dev)

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key


def parse_specifiers(text):
    result = []
    for item in text.strip().strip('()').split(','):
        if not item.strip():
            continue
        match = SPEC_RE.fullmatch(item.strip())
        if match is None:
            raise AppError(f"Неверное ограничение версии: {item}")
        operation, version = match.groups()
        if operation != '===':
            Version(version.removesuffix('.*'))
        if version.endswith('.*') and operation not in {'==', '!='}:
            raise AppError(f"Недопустимая маска версии: {item}")
        if operation == '~=':
            if len(Version(version).release) < MIN_COMPATIBLE_PARTS:
                raise AppError(f"Для ~= нужны хотя бы две части: {version}")
        result.append((operation, version))
    return result


def matches(version, specifiers):
    current = Version(version)
    return all(_matches_one(current, op, value)
               for op, value in parse_specifiers(specifiers))


def _matches_one(current, operation, text):
    if operation == '===':
        return current.text.lower() == text.lower()
    if text.endswith('.*'):
        equal = _prefix_matches(current, Version(text[:-2]))
        return equal if operation == '==' else not equal
    bound = Version(text)
    if operation == '~=':
        prefix = '.'.join(map(str, bound.release[:-1]))
        prefix = f'{bound.epoch}!{prefix}'
        return current >= bound and _prefix_matches(current, Version(prefix))
    left = current.key
    right = bound.key
    if not bound.local:
        left, right = left[:-1], right[:-1]
    if _excluded_boundary(current, bound, operation):
        return False
    return OPERATORS[operation](left, right)


def _prefix_matches(current, bound):
    length = len(bound.release)
    release = current.release + (0,) * length
    return (current.epoch == bound.epoch
            and release[:length] == bound.release)


def _excluded_boundary(current, bound, operation):
    same_release = current.key[:2] == bound.key[:2]
    if not same_release:
        return False
    if operation == '<' and not bound.prerelease:
        return current.prerelease
    if operation == '>' and bound.post == NO_POST:
        return current.post != NO_POST
    return False
