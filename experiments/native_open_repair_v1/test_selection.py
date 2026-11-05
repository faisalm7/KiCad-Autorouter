"""Pure selector controls only; synthetic findings establish no Native support."""
import copy
import hashlib
import unittest
import uuid

from autorouter import pipeline as p, sexpr as sx
from experiments.native_open_repair_v1.selection import derive


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-open-repair/' + name))


def fixture():
    tree = sx.parse('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) '
                    '(net 0 "") (net 1 "KEEP") (net 2 "ONE") (net 3 "TWO"))')
    for index, (net, code) in enumerate([('ONE', 2), ('ONE', 2), ('TWO', 3), ('TWO', 3)]):
        tree.append(sx.parse(f'(footprint "Owned" (uuid "{uid("fp" + str(index))}") '
            f'(property "Reference" "J{index + 1}") (pad "1" smd rect (layers "F.Cu") '
            f'(net {code} "{net}") (uuid "{uid("pad" + str(index))}")))'))
    tree.append(sx.parse(f'(segment (start 0 0) (end 1 1) (width .2) '
        f'(layer "F.Cu") (net 1) (uuid "{uid("kept")}"))'))
    findings = [dict(type='unconnected_items', severity='error', items=[dict(uuid=uid('pad' + str(i))),
        dict(uuid=uid('pad' + str(i + 1)))]) for i in (0, 2)]
    return tree, dict(opens=2, blocking=0, warnings=0, exclusions=0, ignored_checks=[], findings=findings)


def call(tree, native, **changes):
    raw = (sx.dump(tree) + '\n').encode()
    return derive(raw, native, **(dict(candidate_sha256=hashlib.sha256(raw).hexdigest(), report_sha256='a' * 64) | changes))


class EmptyOpenPadPairs(unittest.TestCase):
    def test_every_open_net_selected_and_source_is_unchanged(self):
        tree, native = fixture(); before = copy.deepcopy((tree, native))
        proof = call(tree, native)
        self.assertEqual(proof['names'], ['ONE', 'TWO'])
        self.assertEqual(proof['protected_count'], 1)
        self.assertEqual(len(proof['all_open_witnesses']), 2)
        self.assertEqual((tree, native), before)
        self.assertFalse(proof['native_validation_performed'])

    def test_existing_selected_copper_refuses_including_locked_copper(self):
        for lock in ('', ' locked'):
            tree, native = fixture()
            tree.append(sx.parse(f'(segment{lock} (start 0 0) (end 1 1) (width .2) '
                f'(layer "F.Cu") (net 3) (uuid "{uid("selected")}"))'))
            with self.subTest(lock=lock), self.assertRaisesRegex(p.Rejected, 'zero existing copper'):
                call(tree, native)

    def test_no_partial_mapping_or_description_fallback(self):
        for mutation in ('missing', 'mixed', 'same', 'uppercase', 'repeated', 'three', 'excluded', 'missing-row'):
            tree, native = fixture(); rows = native['findings']; items = rows[0]['items']
            if mutation == 'missing': items[0] = dict(uuid=uid('absent'), description='J1 pad ONE')
            if mutation == 'mixed': items[1]['uuid'] = uid('pad2')
            if mutation == 'same': items[1] = copy.deepcopy(items[0])
            if mutation == 'uppercase': items[0]['uuid'] = items[0]['uuid'].upper()
            if mutation == 'repeated': rows[1] = copy.deepcopy(rows[0])
            if mutation == 'three': items.append(dict(uuid=uid('pad2')))
            if mutation == 'excluded': rows[0]['excluded'] = True
            if mutation == 'missing-row': rows.pop()
            with self.subTest(mutation=mutation), self.assertRaises((p.Rejected, ValueError)):
                call(tree, native)

    def test_blocks_unknown_policy_missing_counts_and_hash_changes_refuse(self):
        for mutation in ('blocking', 'critical-warning', 'unknown', 'missing-count', 'zero', 'bad-summary', 'candidate-hash', 'report-hash'):
            tree, native = fixture(); changes = {}
            if mutation == 'blocking': native['blocking'] = 1
            if mutation == 'critical-warning':
                native['warnings'] = 1; native['findings'].append(dict(type='shorting_items', severity='warning', items=[]))
            if mutation == 'unknown': native['findings'].append(dict(type='unknown-check', severity='warning', items=[]))
            if mutation == 'missing-count': native.pop('blocking')
            if mutation == 'zero': native['opens'] = 0
            if mutation == 'bad-summary': native = None
            if mutation == 'candidate-hash': changes['candidate_sha256'] = '0' * 64
            if mutation == 'report-hash': changes['report_sha256'] = 'g' * 64
            with self.subTest(mutation=mutation), self.assertRaises(p.Rejected): call(tree, native, **changes)


if __name__ == '__main__': unittest.main()
