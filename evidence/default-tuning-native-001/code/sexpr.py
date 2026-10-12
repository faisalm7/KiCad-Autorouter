"""Bounded KiCad S-expression reader retaining every atom, including unknown fields."""
import re
from pathlib import Path

TOKEN = re.compile(r'\s+|;[^\n]*|\(|\)|"(?:\\.|[^"\\])*"|[^\s()";]+')
MAX_BYTES = 32 * 1024 * 1024

def parse(text):
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
