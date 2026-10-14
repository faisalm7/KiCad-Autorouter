"""Pure experimental classifier controls; synthetic native summaries prove no routing."""
import copy
import hashlib
import json
import unittest
import uuid

from autorouter import board_floor as g, native_connected as nc, pipeline as p
from autorouter import routing_scope as rs, sexpr as sx
from autorouter.adapter import _parse_dsn


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'native-connected-fixture/' + name))


def raw(tree):
    return (sx.dump(tree) + '\n').encode()


def fixture():
    tree = sx.parse('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) '
                    '(net 0 "") (net 1 "GND") (net 2 "SIGNAL") (setup))')
    for ref, name, code in [('J1', 'GND', 1), ('J2', 'GND', 1), ('J3', 'SIGNAL', 2), ('J4', 'SIGNAL', 2)]:
        tree.append(sx.parse(f'(footprint "Owned" (uuid "{uid(ref)}") (property "Reference" "{ref}") '
                             f'(pad "1" smd rect (layers "F.Cu") (net {code} "{name}") (uuid "{uid(ref+"-pad")}")))'))
    tree.append(sx.parse(f'(zone (net 1) (net_name "GND") (layers "F.Cu") (uuid "{uid("zone")}") '
                         '(polygon (pts (xy 0 0) (xy 2 0) (xy 2 2))) '
                         '(filled_polygon (pts (xy 0 0) (xy 1 0) (xy 1 1))))'))
    tree.append(sx.parse(f'(segment (start 0 0) (end 1 1) (width .2) (layer "F.Cu") '
                         f'(net 1) (uuid "{uid("source-route")}"))'))
    return tree


DSN = b'''(pcb owned (parser (string_quote ")) (structure (rule (width 200)))
    (network (net GND (pins J1-1 J2-1)) (net SIGNAL (pins J3-1 J4-1))
    (class kicad_default GND SIGNAL (circuit (use_via V)) (rule (width 200) (clearance 150)))))'''


def summary(*pairs):
    findings = [{'type': 'unconnected_items', 'severity': 'error',
                 'items': [{'uuid': a}, {'uuid': b}]} for a, b in pairs]
    return {'opens': len(findings), 'blocking': 0, 'warnings': 0, 'exclusions': 0,
            'ignored_checks': [], 'findings': findings}


class NativeConnectedDraft(unittest.TestCase):
    def setUp(self):
        self.original = raw(fixture())
        self.task = raw(g.task_from_source(sx.parse(self.original.decode())))
        filled = sx.parse(self.task.decode())
        sx.children(filled, 'zone')[0].append(['filled_polygon', ['pts', ['xy', '0', '0'], ['xy', '2', '0'], ['xy', '2', '2']]])
        self.filled = raw(filled)
        self.native = summary((uid('J3-pad'), uid('J4-pad')))
        self.dsn = DSN
        self.hashes = {'owned.kicad_pcb': hashlib.sha256(self.original).hexdigest(),
                       'owned.kicad_pro': hashlib.sha256(b'authored original project').hexdigest()}
        self.report_pin = hashlib.sha256(json.dumps(self.native).encode()).hexdigest()

    def derive(self, **changed):
        args = dict(original_bytes=self.original, task_bytes=self.task, filled_bytes=self.filled,
                    native=self.native, native_dsn=self.dsn, source_hashes=self.hashes,
                    source_name='owned.kicad_pcb', report_sha256=self.report_pin)
        return nc.derive(**(args | changed))

    def check(self, record, **changed):
        args = dict(original_bytes=self.original, task_bytes=self.task, filled_bytes=self.filled,
                    native=self.native, native_dsn=self.dsn, source_hashes=self.hashes,
                    source_name='owned.kicad_pcb', report_sha256=self.report_pin)
        return nc.verify_record(record, **(args | changed))

    def test_inner_copper_and_footprint_zone_scopes_explicitly_refuse(self):
        for mode in ('inner', 'nested-zone'):
            original = sx.parse(self.original.decode())
            if mode == 'inner':
                sx.one(original, 'layers').insert(2, ['4', '"In1.Cu"', 'signal'])
                sx.one(sx.children(sx.children(original, 'footprint')[0], 'pad')[0], 'layers')[:] = ['layers', '"In1.Cu"']
                reason = 'two outer copper'
            else:
                nested = copy.deepcopy(sx.children(original, 'zone')[0])
                sx.one(nested, 'uuid')[1] = '"' + uid('nested-zone') + '"'
                sx.children(original, 'footprint')[0].append(nested)
                reason = 'footprint zones'
            task = raw(g.task_from_source(original))
            hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
            with self.subTest(mode=mode), self.assertRaisesRegex(p.Rejected, reason):
                self.derive(original_bytes=raw(original), task_bytes=task, filled_bytes=task, source_hashes=hashes)

    def test_same_net_repeated_physical_pads_require_every_native_alias(self):
        original = sx.parse(self.original.decode())
        fp = sx.children(original, 'footprint')[0]
        duplicate = copy.deepcopy(sx.children(fp, 'pad')[0])
        sx.one(duplicate, 'uuid')[1] = '"' + uid('J1-duplicate') + '"'
        fp.append(duplicate)
        task = raw(g.task_from_source(original))
        hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
        dsn = self.dsn.replace(b'J1-1 J2-1', b'J1-1 J1-1@1 J2-1')
        args = dict(original_bytes=raw(original), task_bytes=task, filled_bytes=task, source_hashes=hashes)
        record = self.derive(native_dsn=dsn, **args)
        self.assertEqual(record['complete_terminal_count'], 5)
        self.assertEqual(record['inactive_names'], ['GND'])
        for invalid in (self.dsn, dsn.replace(b'J1-1@1', b'J1-1@2'),
                        dsn.replace(b'J3-1 J4-1', b'J3-1 J4-1 J1-1@1')):
            with self.subTest(dsn=invalid), self.assertRaises(p.Rejected):
                self.derive(native_dsn=invalid, **args)
        sx.one(duplicate, 'net')[:] = ['net', '2', '"SIGNAL"']
        task = raw(g.task_from_source(original))
        hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
        with self.assertRaisesRegex(p.Rejected, 'repeated connectivity terminal net'):
            self.derive(original_bytes=raw(original), task_bytes=task, filled_bytes=task, source_hashes=hashes)

    def test_real_at_sign_pad_number_cannot_collide_with_exporter_alias(self):
        original = sx.parse(self.original.decode())
        sx.children(sx.children(original, 'footprint')[0], 'pad')[0][1] = '"1@1"'
        task = raw(g.task_from_source(original))
        hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
        with self.assertRaisesRegex(p.Rejected, 'reserved connectivity terminal alias'):
            self.derive(original_bytes=raw(original), task_bytes=task, filled_bytes=task, source_hashes=hashes)

    def test_distinct_reference_number_pairs_cannot_merge_by_token_collision(self):
        original = sx.parse(self.original.decode())
        for fp, reference, number in zip(sx.children(original, 'footprint')[:2], ('J', 'J-1'), ('1-1', '1')):
            sx.children(fp, 'property')[0][2] = '"' + reference + '"'
            sx.children(fp, 'pad')[0][1] = '"' + number + '"'
        task = raw(g.task_from_source(original))
        hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
        with self.assertRaisesRegex(p.Rejected, 'ambiguous connectivity DSN terminal'):
            self.derive(original_bytes=raw(original), task_bytes=task, filled_bytes=task, source_hashes=hashes)

    def test_positive_hint_is_whole_net_only_and_never_accepts_routing(self):
        record = self.derive()
        self.assertEqual(record['active_names'], ['SIGNAL'])
        self.assertEqual(record['inactive_names'], ['GND'])
        self.assertEqual(record['complete_terminal_count'], 4)
        self.assertFalse(record['routing_accepted'])
        emitted, binding = nc.partition(self.dsn, self.dsn, record)
        self.assertIn('--router.autorouter.ignore_net_classes=', binding['engine_argument'])
        self.assertEqual(sx.children(sx.one(_parse_dsn(emitted.decode()), 'network'), 'net'),
                         sx.children(sx.one(_parse_dsn(self.dsn.decode()), 'network'), 'net'))

    def test_separate_ground_island_and_pad_zone_findings_keep_entire_net_active(self):
        for pair in [(uid('J1-pad'), uid('J2-pad')), (uid('J1-pad'), uid('zone'))]:
            record = self.derive(native=summary((uid('J3-pad'), uid('J4-pad')), pair))
            self.assertEqual(record['inactive_names'], [])
            emitted, binding = nc.partition(self.dsn, self.dsn, record)
            self.assertEqual(emitted, self.dsn)
            self.assertIsNone(binding['engine_argument'])

    def test_unknown_null_mixed_or_repeated_open_endpoints_refuse(self):
        null_tree = sx.parse(self.filled.decode())
        sx.one(sx.children(sx.children(null_tree, 'footprint')[0], 'pad')[0], 'net')[:] = ['net', '0', '""']
        for pair in [(uid('unknown'), uid('J4-pad')), (None, uid('J4-pad')),
                     (uid('J1-pad'), uid('J4-pad')), (uid('J3-pad'), uid('J3-pad'))]:
            with self.subTest(pair=pair), self.assertRaises(p.Rejected):
                self.derive(native=summary(pair))
        with self.assertRaises(p.Rejected):
            self.derive(filled_bytes=raw(null_tree), native=summary((uid('J1-pad'), uid('zone'))))

    def test_ambiguous_footprint_or_uuid_endpoint_refuses(self):
        original = sx.parse(self.original.decode())
        fp = sx.children(original, 'footprint')[0]
        fp.append(sx.parse(f'(pad "2" smd rect (layers "F.Cu") (net 2 "SIGNAL") (uuid "{uid("mixed-pad")}"))'))
        task = raw(g.task_from_source(original))
        dsn = self.dsn.replace(b'J3-1 J4-1', b'J3-1 J4-1 J1-2')
        hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
        with self.assertRaisesRegex(p.Rejected, 'ambiguous task connectivity endpoint'):
            self.derive(original_bytes=raw(original), task_bytes=task, filled_bytes=task,
                        source_hashes=hashes, native_dsn=dsn, native=summary((uid('J1'), uid('J4-pad'))))
        filled = sx.parse(self.filled.decode())
        sx.one(sx.children(filled, 'footprint')[1], 'uuid')[1] = '"' + uid('J1') + '"'
        with self.assertRaises(p.Rejected):
            self.derive(filled_bytes=raw(filled))

    def test_source_routes_and_stale_stored_fill_cannot_classify(self):
        self.assertFalse(p.routes(sx.parse(self.task.decode())))
        self.assertFalse(sx.children(sx.children(sx.parse(self.task.decode()), 'zone')[0], 'filled_polygon'))
        with self.assertRaisesRegex(p.Rejected, 'task differs'):
            self.derive(task_bytes=self.original, filled_bytes=self.original)
        changed = sx.parse(self.task.decode())
        changed.append(['property', '"changed original"', '"yes"'])
        with self.assertRaisesRegex(p.Rejected, 'saved refill changed'):
            self.derive(filled_bytes=raw(changed))

    def test_protected_source_explicitly_refuses_and_never_unlocks(self):
        original = sx.parse(self.original.decode())
        p.routes(original)[0].append(['locked', 'yes'])
        with self.assertRaisesRegex(ValueError, 'protected routes'):
            self.derive(original_bytes=raw(original))

    def test_missing_added_reassigned_terminal_or_changed_class_refuses(self):
        for dsn in [self.dsn.replace(b'J1-1 J2-1', b'J1-1'),
                    self.dsn.replace(b'J1-1 J2-1', b'J1-1 J2-1 UNKNOWN-1'),
                    self.dsn.replace(b'J1-1 J2-1', b'J1-1 J4-1')]:
            with self.subTest(dsn=dsn), self.assertRaises(p.Rejected):
                self.derive(native_dsn=dsn)
        record = self.derive()
        with self.assertRaisesRegex(p.Rejected, 'terminal/class constraints'):
            nc.partition(self.dsn, self.dsn.replace(b'width 200', b'width 100'), record)

    def test_source_report_companion_and_dsn_pins_are_retained(self):
        record = self.derive()
        self.assertEqual(self.check(record), record)
        for changed in [dict(report_sha256='0' * 64),
                        dict(source_hashes=self.hashes | {'owned.kicad_pro': '0' * 64})]:
            with self.subTest(changed=changed), self.assertRaisesRegex(p.Rejected, 'classification changed'):
                self.check(record, **changed)
        with self.assertRaisesRegex(p.Rejected, 'original-project/report pins'):
            self.derive(source_hashes=self.hashes | {'owned.kicad_pcb': '0' * 64})
        with self.assertRaisesRegex(p.Rejected, 'stale'):
            nc.partition(self.dsn + b' ', self.dsn, record)
        for key in ('native_report_sha256', 'source_hashes', 'active_names', 'inactive_names', 'policy'):
            altered = copy.deepcopy(record)
            del altered[key]
            with self.subTest(key=key), self.assertRaisesRegex(p.Rejected, 'classification changed'):
                self.check(altered)

    def test_null_native_net_endpoint_refuses_even_when_other_nets_map(self):
        original = sx.parse(self.original.decode())
        original.append(sx.parse(f'(footprint "Owned" (uuid "{uid("NP")}") (property "Reference" "NP") '
                                 f'(pad "1" np_thru_hole circle (layers "*.Cu") (net 0 "") (uuid "{uid("NP-pad")}")))'))
        task = raw(g.task_from_source(original))
        hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
        with self.assertRaisesRegex(p.Rejected, 'null or ambiguous'):
            self.derive(original_bytes=raw(original), task_bytes=task, filled_bytes=task,
                        source_hashes=hashes, native=summary((uid('NP-pad'), uid('zone'))))

    def test_engine_settings_keep_existing_completion_only_guards(self):
        record = self.derive()
        _, binding = nc.partition(self.dsn, self.dsn, record)
        settings = nc.engine_settings(100, binding)
        self.assertEqual(settings['profile'], 'completion-only')
        for argument in ('--router.fanout.enabled=false', '--router.optimizer.enabled=false',
                         '--router.automatic_neckdown=false', '--router.neck_width_um=0', binding['engine_argument']):
            self.assertIn(argument, settings['argv'])

    def test_excluded_disabled_or_incomplete_native_findings_never_inactive(self):
        for native in [self.native | {'opens': 2}, self.native | {'exclusions': 1},
                       self.native | {'ignored_checks': [{'key': 'unconnected_items'}]},
                       self.native | {'blocking': 1}]:
            with self.subTest(native=native), self.assertRaises(p.Rejected):
                self.derive(native=native)
        with self.assertRaisesRegex(p.Rejected, 'no-engine path'):
            self.derive(native=summary())

    def test_public_selection_bound_is_unchanged_and_large_internal_scope_refuses(self):
        with self.assertRaises(ValueError):
            rs.validate_names(['NET' + str(i) for i in range(65)])
        original = sx.parse(self.original.decode())
        original.extend([['net', str(i + 3), '"NET' + str(i) + '"'] for i in range(63)])
        task = raw(g.task_from_source(original))
        hashes = self.hashes | {'owned.kicad_pcb': hashlib.sha256(raw(original)).hexdigest()}
        with self.assertRaisesRegex(p.Rejected, 'complete net population'):
            self.derive(original_bytes=raw(original), task_bytes=task, filled_bytes=task, source_hashes=hashes)


class ProbePublicationTests(unittest.TestCase):
    def test_explicit_project_outside_owned_run_scope_refuses_before_native(self):
        import tempfile
        from pathlib import Path
        from experiments.native_connected_v1 import driver as d
        output = d.ROOT / '.runs' / ('unused-connectivity-control-' + str(uuid.uuid4()))
        with tempfile.TemporaryDirectory() as scratch:
            with self.assertRaisesRegex(p.Rejected, 'owned diagnostic source'):
                d.experiment(output, project=Path(scratch) / 'not-read.kicad_pcb')
        self.assertFalse(output.exists())

    def test_actual_shared_publication_keeps_only_current_probe_qualification(self):
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from experiments.native_connected_v1 import driver as d
        for action in ('unchanged', 'mutated', 'cancelled'):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as scratch:
                output = Path(scratch).resolve()
                material = output / 'actual-material'
                material.write_bytes(b'unchanged')
                completed = d.f.evidence_inventory(output)
                record = dict(accepted=False, status='completed', eligibility_qualified=True)
                job = SimpleNamespace(steps=[])
                started = d.time.monotonic()
                cpu = d.time.process_time() + d.f.child_cpu()
                def stable():
                    if d.f.evidence_inventory(output) != completed:
                        raise p.Rejected('completed evidence changed')
                def account():
                    d.account_probe(record, job, started, cpu, lambda: 30)
                def final_check():
                    if action == 'cancelled':
                        raise KeyboardInterrupt
                    if action == 'mutated':
                        material.write_bytes(b'changed')
                    stable()
                d.f.publish(output, record, stable, account, lambda: 30, final_check=final_check)
                self.assertFalse(record['accepted'])
                self.assertEqual(record['eligibility_qualified'], action == 'unchanged')
                expected = {'unchanged': 'completed', 'mutated': 'invalidated', 'cancelled': 'cancelled'}[action]
                self.assertEqual(record['status'], expected)
                stored = d.f.read_json(output / 'result.json')
                self.assertEqual(stored['eligibility_qualified'], action == 'unchanged')
                self.assertEqual(stored['status'], expected)


if __name__ == '__main__':
    unittest.main()
