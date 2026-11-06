"""Pure original-to-prepared placement qualification boundaries.

These tests use project-owned AST fixtures and synthetic Native witness records.
They do not run KiCad, attest real Native observations, or grant approval.
"""
import copy
import hashlib
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from autorouter import gui, placement, placement_copper as copper, placement_intent as intent
from autorouter import pipeline, sexpr as sx
from experiments.placement_native_proposal_v1 import contract, multipad_fixture, ordinary_fixture
from tests.test_placement_copper import REGION, raw, route, source_tree


def synthetic_details(observation):
    """Representative witness shape; deliberately no claim of Native capture."""
    names = sorted({pad['net'] for fp in observation['footprints'] for pad in fp['pads']}
                   | {item['net'] for item in observation['routes']})
    codes = {name: index + 1 for index, name in enumerate(names)}
    return dict(native_pad_netcodes={pad['uuid']: codes[pad['net']]
                                    for fp in observation['footprints'] for pad in fp['pads']},
                native_route_netcodes={item['uuid']: codes[item['net']]
                                      for item in observation['routes']},
                actual_native_areas=dict(zones=[dict(uuid='owned-zone-witness',
                    outlines_nm=[[[7000000, 22000000], [30000000, 22000000], [30000000, 28000000]]],
                    holes=[], layers=['B.Cu'], is_rule_area=False)],
                    footprint_zone_count=0, footprint_rulearea_count=0))


class RetainedNativeCopperDetails(unittest.TestCase):
    def setUp(self):
        self.source = raw(source_tree())
        self.plan = copper.propose(self.source, ordinary_fixture.selected())
        self.observation = contract.inspect_board(self.source, scope=contract.ORDINARY_SCOPE)
        self.details = synthetic_details(self.observation)

    def test_only_reviewed_routes_disappear_for_both_product_scopes(self):
        multi = multipad_fixture.board(); multi.append(route('qualification-multipad', 'ROUTE_A'))
        cases = [(self.source, ordinary_fixture.selected(), contract.ORDINARY_SCOPE),
                 (raw(multi), [multipad_fixture.uid(ref + '-footprint') for ref in ('J1', 'J2')],
                  contract.MULTIPAD_SCOPE)]
        for source, selected, scope in cases:
            with self.subTest(scope=scope):
                plan = copper.propose(source, selected)
                details = synthetic_details(contract.inspect_board(source, scope=scope))
                original = copy.deepcopy(details); original_plan = copy.deepcopy(plan)
                result = placement._retained_native_details(details, plan)
                removed = {row['uuid'] for row in plan['removed_routes']}
                self.assertEqual(set(original['native_route_netcodes']) - set(result['native_route_netcodes']), removed)
                self.assertEqual(result['native_route_netcodes'],
                    {key: value for key, value in original['native_route_netcodes'].items() if key not in removed})
                self.assertEqual(result['native_pad_netcodes'], original['native_pad_netcodes'])
                self.assertEqual(result['actual_native_areas'], original['actual_native_areas'])
                self.assertEqual(details, original); self.assertEqual(plan, original_plan)
                # Mutating returned maps or nested area geometry must not alter
                # the retained original source witness.
                result['native_pad_netcodes'].clear()
                result['actual_native_areas']['zones'][0]['outlines_nm'][0][0][0] = 99
                self.assertEqual(details, original)

    def test_preserve_policy_keeps_complete_detached_witness(self):
        result = placement._retained_native_details(self.details, None)
        self.assertEqual(result, self.details)
        result['native_route_netcodes'].clear()
        self.assertTrue(self.details['native_route_netcodes'])

    def test_missing_extra_or_type_substituted_witness_fields_refuse(self):
        cases = [None, [], {}]
        for key in self.details:
            altered = copy.deepcopy(self.details); altered.pop(key); cases.append(altered)
        extra = copy.deepcopy(self.details); extra['approved'] = True; cases.append(extra)
        for key in self.details:
            altered = copy.deepcopy(self.details); altered[key] = []; cases.append(altered)
        empty_pads = copy.deepcopy(self.details); empty_pads['native_pad_netcodes'] = {}; cases.append(empty_pads)
        for case in cases:
            for plan in (None, self.plan):
                with self.subTest(case=case, policy=plan is not None), self.assertRaises(ValueError):
                    placement._retained_native_details(case, plan)

    def test_boolean_float_nonpositive_or_untyped_net_codes_refuse(self):
        for field in ('native_pad_netcodes', 'native_route_netcodes'):
            identity = next(iter(self.details[field]))
            for value in (True, False, 1.0, 0, -1, '1', None):
                altered = copy.deepcopy(self.details); altered[field][identity] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    placement._retained_native_details(altered, self.plan)
            altered = copy.deepcopy(self.details); value = altered[field].pop(identity); altered[field][1] = value
            with self.subTest(field=field, nonstring_identity=True), self.assertRaises(ValueError):
                placement._retained_native_details(altered, self.plan)

    def test_missing_replaced_extra_or_duplicate_removed_identity_refuses(self):
        removed = self.plan['removed_routes'][0]['uuid']; kept = self.plan['protected_routes'][0]['uuid']
        for mode in ('missing_removed', 'missing_kept', 'same_count_substitution', 'extra', 'wrong_count', 'duplicate_removed', 'wrong_kept'):
            details = copy.deepcopy(self.details); plan = copy.deepcopy(self.plan)
            if mode == 'missing_removed': details['native_route_netcodes'].pop(removed)
            elif mode == 'missing_kept': details['native_route_netcodes'].pop(kept)
            elif mode == 'same_count_substitution':
                details['native_route_netcodes']['unapproved-replacement'] = details['native_route_netcodes'].pop(kept)
            elif mode == 'extra': details['native_route_netcodes']['unapproved-extra'] = 1
            elif mode == 'wrong_count': plan['original_route_count'] += 1
            elif mode == 'duplicate_removed': plan['removed_routes'].append(copy.deepcopy(plan['removed_routes'][0]))
            else: plan['protected_routes'][0]['uuid'] = 'wrong-retained-route'
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                placement._retained_native_details(details, plan)


class PreparedSourceQualification(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='placement-copper-qualification-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.board = ordinary_fixture.write_project(self.root / 'owned source')
        self.raw = raw(source_tree()); self.board.write_bytes(self.raw)
        self.inspection = intent.inspect_saved(self.board)
        self.settings = intent.settings(ordinary_fixture.selected(), REGION, scope=contract.ORDINARY_SCOPE,
                                       copper_policy=intent.COPPER_POLICY)
        self.plan = intent.copper_plan(self.inspection, self.settings)
        self.binding = dict(inspection=copy.deepcopy(self.inspection),
            intent=dict(settings=copy.deepcopy(self.settings), copper_plan=copy.deepcopy(self.plan)))

    def test_prepared_source_is_exact_composed_task_and_original_is_unchanged(self):
        inventory = gui.source_inventory(self.board); binding = copy.deepcopy(self.binding)
        with patch('subprocess.Popen', side_effect=AssertionError('Pure qualification boundary may not start Native')):
            plan, prepared = placement._prepared_source(binding, self.raw)
        self.assertEqual(plan, self.plan)
        self.assertEqual(prepared, copper.prepare(self.raw, self.plan))
        self.assertEqual(hashlib.sha256(prepared).hexdigest(), plan['task_sha256'])
        self.assertEqual({contract.uid(item) for item in pipeline.routes(sx.parse(prepared.decode()))},
                         {item['uuid'] for item in plan['protected_routes']})
        self.assertEqual(gui.source_inventory(self.board), inventory)
        self.assertEqual(self.binding, binding)
        self.assertEqual(self.board.read_bytes(), self.raw)

    def test_plan_tampering_missing_or_re_signed_protection_is_refused(self):
        for mode in ('absent', 'missing_protected', 'removed_unrelated', 'changed_net', 'false_authority', 'different_source', 'extra_field'):
            binding = copy.deepcopy(self.binding)
            if mode == 'absent': binding['intent'].pop('copper_plan')
            else:
                plan = binding['intent']['copper_plan']
                if mode == 'missing_protected': plan['protected_routes'].clear()
                elif mode == 'removed_unrelated': plan['removed_routes'].append(plan['protected_routes'].pop())
                elif mode == 'changed_net': plan['incident_names'] = ['GND']
                elif mode == 'false_authority': plan['approval_granted'] = True
                elif mode == 'different_source': plan['source_sha256'] = '0' * 64
                else: plan['silently_allow_partial_removal'] = True
                plan['plan_sha256'] = hashlib.sha256(intent.constraints.encoded(
                    {key: value for key, value in plan.items() if key != 'plan_sha256'})).hexdigest()
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                placement._prepared_source(binding, self.raw)

    def test_changed_snapshot_or_original_board_refuses_saved_plan(self):
        with self.assertRaises(ValueError): placement._prepared_source(self.binding, self.raw + b'\n')
        self.board.write_bytes(self.raw + b'\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            placement._prepared_source(self.binding, self.raw)

    def test_changed_sidecar_refuses_even_when_pcb_bytes_are_unchanged(self):
        for suffix in ('.kicad_pro', '.kicad_sch', '.kicad_prl'):
            sidecar = self.board.with_suffix(suffix)
            before = sidecar.read_bytes()
            try:
                sidecar.write_bytes(before + b'\n')
                with self.subTest(suffix=suffix), self.assertRaisesRegex(ValueError, 'source changed'):
                    placement._prepared_source(self.binding, self.raw)
            finally: sidecar.write_bytes(before)
        self.assertEqual(gui.source_inventory(self.board), self.inspection['source_hashes'])

    def test_protection_added_after_review_refuses_old_removal_plan(self):
        for field, value in (('protected_names', ['ROUTE_A']),
                             ('protected_route_ids', [self.plan['removed_routes'][0]['uuid']])):
            binding = copy.deepcopy(self.binding); binding['intent']['settings'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                placement._prepared_source(binding, self.raw)

    def test_old_policies_cannot_carry_removal_authority(self):
        for scope in (contract.MULTIPAD_SCOPE, contract.ORDINARY_SCOPE):
            settings = intent.settings(ordinary_fixture.selected(), REGION, scope=scope)
            binding = copy.deepcopy(self.binding); binding['intent'] = dict(settings=settings)
            self.assertEqual(placement._prepared_source(binding, self.raw), (None, self.raw))
            binding['intent']['copper_plan'] = copy.deepcopy(self.plan)
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, 'unexpected copper-removal authority'):
                placement._prepared_source(binding, self.raw)

    def test_only_v3_gets_a_distinct_prepared_project_path(self):
        output = self.root / 'output'
        old_bindings = [dict(inspection=self.inspection)]
        for scope in (contract.MULTIPAD_SCOPE, contract.ORDINARY_SCOPE):
            old_bindings.append(dict(inspection=self.inspection,
                intent=dict(settings=intent.settings(ordinary_fixture.selected(), REGION, scope=scope))))
        for binding in old_bindings:
            work, paths = placement._paths(output, binding)
            self.assertEqual(set(paths), {'snapshot', 'candidate', 'refill-preimage', 'refill-native'})
            self.assertTrue(all(path.parent.parent == work for path in paths.values()))
        work, paths = placement._paths(output, self.binding)
        self.assertEqual(set(paths), {'snapshot', 'candidate', 'refill-preimage', 'refill-native', 'prepared'})
        self.assertEqual(paths['prepared'], work / 'prepared' / self.board.name)
        self.assertEqual(len(set(paths.values())), 5)
        self.assertFalse(output.exists())


if __name__ == '__main__': unittest.main()
