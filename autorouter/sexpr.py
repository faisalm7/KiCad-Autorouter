"""Bounded KiCad S-expression reader retaining every atom, including unknown fields."""
import re
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from marshal import dumps as _clone_encode, loads as _clone_decode

TOKEN = re.compile(r'\s+|;[^\n]*|\(|\)|"(?:\\.|[^"\\])*"|[^\s()";]+')
MAX_BYTES = 32 * 1024 * 1024
MEMO_BYTES = 8 * 1024 * 1024
MEMO_NODES = 250000
MEMO_ENTRIES = 64
_parse_session = ContextVar('autorouter_sexpr_parse_session', default=None)


def clone(tree):
    """Copy list/string syntax, preserving aliases and mutation independence.

    The decoder receives only bytes made here from checked built-in values;
    it never reads a file or caller-supplied serialized data. This is a pure
    copy, not a syntax/result cache. Keep the codec callables visible to the
    shared live-policy identity. Explicit format4 works in both pinned Pythons.
    """
    pending = [tree]; seen = set()
    while pending:
        node = pending.pop()
        if type(node) is str:continue
        if type(node) is not list:raise TypeError('S-expression list or atom required')
        identity = id(node)
        if identity in seen:continue
        seen.add(identity); pending.extend(node)
    return _clone_decode(_clone_encode(tree, 4))


def _parse_uncached(text):
    if len(text.encode()) > MAX_BYTES:
        raise ValueError('board exceeds 32 MiB limit')
    stack, root, end = [], [], 0
    for m in TOKEN.finditer(text):
        if m.start() != end:
            raise ValueError('invalid S-expression token')
        end = m.end()
        t = m.group()
        if t.isspace() or t.startswith(';'):
            continue
        if t == '(':
            if len(stack) > 128:
                raise ValueError('S-expression nesting limit')
            item = []
            (stack[-1] if stack else root).append(item)
            stack.append(item)
        elif t == ')':
            if not stack:
                raise ValueError('unmatched closing parenthesis')
            stack.pop()
        else:
            if not stack:
                raise ValueError('atom outside root')
            stack[-1].append(t)
    if end != len(text) or stack or len(root) != 1:
        raise ValueError('incomplete S-expression')
    return root[0]


@contextmanager
def parsing_session():
    """Reuse pure syntax only inside one operation; never cache file reads.

    Stored trees are immutable, bounded by input bytes and tree nodes. Every
    caller gets its own mutable lists. Nested operations share the same memo;
    an error or cancellation clears it, and the outer exit retains nothing.
    """
    existing = _parse_session.get()
    state = existing if existing is not None else dict(entries={}, bytes=0, nodes=0, policy=None)
    token = _parse_session.set(state)
    try:
        yield
    except BaseException:
        state.update(entries={}, bytes=0, nodes=0)
        raise
    finally:
        if existing is None:state.update(entries={}, bytes=0, nodes=0)
        _parse_session.reset(token)


def _freeze_tree(tree, remaining):
    remaining[0] -= 1
    if remaining[0] < 0:raise OverflowError('syntax memo node bound')
    if type(tree) is str:return tree
    if type(tree) is not list:raise TypeError('syntax memo requires parser lists and atoms')
    return tuple(_freeze_tree(item, remaining) for item in tree)


def _thaw_tree(tree):
    return [_thaw_tree(item) if type(item) is tuple else item for item in tree]


def parse(text):
    state = _parse_session.get()
    if state is None:return _parse_uncached(text)
    try:
        # A changed live tokenizer, parser body or bound cannot inherit syntax
        # derived under the previous policy. This is not a file/stat cache.
        policy = (TOKEN, MAX_BYTES, MEMO_BYTES, MEMO_NODES, MEMO_ENTRIES,
                  _parse_uncached, getattr(_parse_uncached, '__code__', None),
                  _freeze_tree, _thaw_tree)
        if state['policy'] != policy:
            state.update(entries={}, bytes=0, nodes=0, policy=policy)
        size = len(text.encode())
        if size > MAX_BYTES:raise ValueError('board exceeds 32 MiB limit')
        entry = state['entries'].pop(text, None)
        if entry is not None:
            state['entries'][text] = entry  # Keep frequently reused source syntax resident.
            return _thaw_tree(entry[0])
        tree = _parse_uncached(text)
        if size > MEMO_BYTES or MEMO_ENTRIES < 1 or MEMO_NODES < 1:return tree
        remaining = [MEMO_NODES]
        try:frozen = _freeze_tree(tree, remaining)
        except OverflowError:return tree  # Valid large input, simply uncached.
        nodes = MEMO_NODES - remaining[0]
        while state['entries'] and (len(state['entries']) >= MEMO_ENTRIES
                or state['bytes'] + size > MEMO_BYTES or state['nodes'] + nodes > MEMO_NODES):
            first = next(iter(state['entries']))
            _, old_bytes, old_nodes = state['entries'].pop(first)
            state['bytes'] -= old_bytes; state['nodes'] -= old_nodes
        state['entries'][text] = (frozen, size, nodes)
        state['bytes'] += size; state['nodes'] += nodes
        return tree
    except BaseException:
        state.update(entries={}, bytes=0, nodes=0)
        raise

def read(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ValueError('board exceeds 32 MiB limit')
    return parse(p.read_text())

def dump(node):
    if isinstance(node, str):
        return node
    return '(' + ' '.join(dump(v) for v in node) + ')'

def write(path, node):
    Path(path).write_text(dump(node) + '\n')

def children(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]

def one(node, key, default=None):
    a = children(node, key)
    if len(a) > 1:
        raise ValueError('duplicate singleton ' + key)
    return a[0] if a else default

def unquote(atom):
    if atom.startswith('"'):
        # KiCad uses C-style quote and backslash escaping; do not decode Unicode bytes.
        return re.sub(r'\\(["\\])', r'\1', atom[1:-1])
    return atom
