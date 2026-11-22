import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from autorouter import finish_gaps, pipeline, routing_scope, sexpr
from tests import test_native_connected as connected


class FinishGapsTest(unittest.TestCase):
    def setUp(self):
        self.board = connected.fixture()
        self.pins = connected.uid('J3-pad'), connected.uid('J4-pad')
        self.native = connected.summary(self.pins)
        self.before = {'owned.kicad_pcb': 'a' * 64}

    def test_only_verified_open_nets_are_selected(self):
        plan = finish_gaps.plan(self.board, self.before, self.native)
        self.assertEqual(plan['nets'], ['SIGNAL'])
        self.assertEqual(plan['protected_routes'], 1)
        finish_gaps.require_ready(plan, plan['binding_sha256'])
        changed = finish_gaps.plan(self.board, {'owned.kicad_pcb': 'b' * 64}, self.native)
        with self.assertRaisesRegex(pipeline.Rejected, 'preview no longer matches'):
            finish_gaps.require_ready(changed, plan['binding_sha256'])
        self.assertEqual(finish_gaps.plan(self.board, self.before, connected.summary())['status'], 'already_connected')

    def test_ambiguous_or_weakened_open_never_expands_to_other_nets(self):
        mixed = connected.summary((self.pins[0], connected.uid('J1-pad')))
        self.assertEqual(finish_gaps.plan(self.board, self.before, mixed)['status'], 'unsupported')
        weakened = connected.summary(self.pins)
        weakened['findings'][0]['excluded'] = True
        refused = finish_gaps.plan(self.board, self.before, weakened)
        self.assertEqual((refused['status'], refused['nets']), ('blocked', []))

    def test_source_policy_names_the_blocking_native_field_and_remedy(self):
        self.native['warnings'] = 2
        self.native['findings'].extend([
            {'type': 'footprint_symbol_field_mismatch', 'severity': 'warning',
             'description': "Field 'Datasheet' differs (PCB: '~', Schematic: '')", 'items': [{'description': 'Footprint J2'}]},
            {'type': 'footprint_symbol_mismatch', 'severity': 'warning',
             'description': 'Symbol and placed footprint identifiers differ', 'items': [{'description': 'Footprint J1'}]},
        ])
        plan = finish_gaps.plan(self.board, self.before, self.native)
        self.assertEqual((plan['status'], plan['nets']), ('blocked', []))
        text = '\n'.join(finish_gaps.source_delivery_lines(plan['source_delivery']))
        for part in ("KiCad warning", 'J2', "PCB: '~'", "Schematic: ''", 'J1', 'Copperpath blocks delivery', 'Save the PCB and schematic'):
            self.assertIn(part, text)
        self.assertFalse(pipeline.native_accepted(self.native))

    def test_preserve_all_includes_existing_copper_on_active_net(self):
        retained = sexpr.clone(pipeline.routes(self.board)[0])
        net = sexpr.one(retained, 'net')
        net[1] = '2'
        sexpr.one(retained, 'uuid')[1] = '"' + connected.uid('already-on-active') + '"'
        self.board.append(retained)
        candidate = sexpr.clone(self.board)
        self.assertEqual(routing_scope.audit(self.board, candidate, ['SIGNAL'], preserve_all=True)['protected_count'], 2)
        candidate.remove(retained)
        with self.assertRaisesRegex(pipeline.Rejected, 'protected route missing'):
            routing_scope.audit(self.board, candidate, ['SIGNAL'], preserve_all=True)
        candidate = sexpr.clone(self.board)
        extra = sexpr.clone(pipeline.routes(candidate)[0])
        sexpr.one(extra, 'uuid')[1] = '"' + connected.uid('extra-off-net') + '"'
        candidate.append(extra)
        with self.assertRaisesRegex(pipeline.Rejected, 'nonselected or unknown net'):
            routing_scope.audit(self.board, candidate, ['SIGNAL'], preserve_all=True)

    def test_current_producer_cannot_drop_scope_proof_to_read_as_historical(self):
        with TemporaryDirectory() as tmp, patch.object(pipeline.c, 'NATIVE_VERSION', '10.0.7'):
            root = Path(tmp).resolve()
            code = root / 'code'
            code.mkdir()
            producer = code / 'pipeline.py'
            def receipt(raw):
                producer.write_bytes(raw)
                return {'scope': 'partial_completion', 'adapter': 'both',
                        'tools': {'implementation_sha256': {'autorouter/pipeline.py': hashlib.sha256(raw).hexdigest()}}}
            historical = receipt(b'# old producer\n')
            self.assertFalse(finish_gaps.required(root, historical, ordinary=True))
            current = receipt(b"FINISH_GAPS_POLICY='native-missing-connections-v1'\n")
            with self.assertRaisesRegex(pipeline.Rejected, 'mandatory producer or scope proof'):
                finish_gaps.required(root, current, ordinary=True)
            self.assertTrue(finish_gaps.required(root, {**current, 'finish_gaps': {}}, ordinary=True))
