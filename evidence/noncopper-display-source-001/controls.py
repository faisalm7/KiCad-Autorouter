"""Bounded pure guard controls; no preflight, Native, engine or project writes."""
import copy
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from autorouter import netclass as n
from autorouter.layer_policy import NONCOPPER

START, CPU0 = time.monotonic(), time.process_time()
FILES = ('autorouter/netclass.py', 'tests/test_four_copper_classes.py')
before = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
base = ['kicad_pcb', ['version', '20260206'], ['layers',
    *[[str(code), json.dumps(name), 'signal'] for code, name in zip(n.FOUR_COPPER_IDS, n.FOUR_COPPER_NAMES)],
    *[[code, json.dumps(name), 'user'] for code, name in NONCOPPER.items()]]]
def row(tree, code='5'):
    return next(item for item in tree[2][1:] if item[0] == code)
def display(tree, value, code='5'):
    row(tree, code).append(json.dumps(value, ensure_ascii=False))
cases = []
def check(name, change, allowed):
    tree = copy.deepcopy(base)
    change(tree)
    original = copy.deepcopy(tree)
    error = None
    try:
        result = n.four_copper_source_layers(tree)
        actual = True
        assert result == list(n.FOUR_COPPER_NAMES)
    except ValueError as exc:
        actual = False
        error = str(exc)
    cases.append(dict(name=name, expected=allowed, actual=actual,
                      unchanged=tree == original, error=error))
check('ordinary_three_atom_rows', lambda t: None, True)
for code, name in NONCOPPER.items():
    check('own_exact_canonical_display_' + code,
          lambda t, c=code, label=name: display(t, label, c), True)
for label in ('F.Adhesive', 'User.Drawings', 'Front "silk" \\ drawing', 'a'*256, 'μ'*128):
    check('valid_label_' + repr(label[:24]), lambda t, label=label: display(t, label), True)
for label in ('f.cu', 'IN1.CU', 'in2.cu', 'b.cu', 'B.SilkS', 'F.Fab', 'User.4',
              '', ' leading', 'trailing ', 'a'*257, 'μ'*129, 'line\nbreak', 'nul\x00byte'):
    check('refuse_label_' + repr(label[:24]), lambda t, label=label: display(t, label), False)
check('casefold_display_collision', lambda t: (display(t, 'Straße'), display(t, 'STRASSE', '7')), False)
check('quoted_escape_collision', lambda t: (display(t, 'Front "silk"'), display(t, 'Front "silk"', '7')), False)
check('physical_id_replaced_by_copper', lambda t: row(t).__setitem__(0, '4'), False)
check('foreign_physical_id', lambda t: row(t).__setitem__(0, '999'), False)
check('foreign_physical_name', lambda t: row(t).__setitem__(1, '"In3.Cu"'), False)
check('recognized_name_wrong_id', lambda t: row(t).__setitem__(1, '"F.Adhes"'), False)
check('hidden_copper_type', lambda t: row(t).__setitem__(2, 'signal'), False)
check('copper_fourth_atom_even_own_name', lambda t: t[2][1].append('"F.Cu"'), False)
check('copper_order', lambda t: t[2].__setitem__(slice(2,4), list(reversed(t[2][2:4]))), False)
check('noncopper_interleaved_in_copper_order', lambda t: t[2].insert(2, t[2].pop(5)), False)
check('nested_display', lambda t: row(t).append(['display', '"Front"']), False)
check('extra_atom', lambda t: row(t).extend(['"Front"', '"extra"']), False)
check('malformed_escape', lambda t: row(t).append('"bad\\q"'), False)
check('unterminated_atom', lambda t: row(t).append('"Front'), False)
after = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
record = dict(kind='pure-four-copper-noncopper-display-guard-controls',
    native_executed=False, engine_executed=False, tests=cases,
    all_passed=all(c['expected'] == c['actual'] and c['unchanged'] for c in cases),
    sources_before=before, sources_after=after, sources_unchanged=before == after,
    wall_seconds=time.monotonic()-START, cpu_seconds=time.process_time()-CPU0)
target = Path(__file__).with_name('controls.json')
target.write_text(json.dumps(record, indent=2, ensure_ascii=True)+'\n')
print(json.dumps(dict(controls=len(cases), all_passed=record['all_passed'],
    sources_unchanged=record['sources_unchanged'], wall_seconds=record['wall_seconds'], cpu_seconds=record['cpu_seconds'])))
raise SystemExit(0 if record['all_passed'] and record['sources_unchanged'] else 1)
