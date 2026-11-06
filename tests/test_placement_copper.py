"""Owned pure affected-net planning controls; no Native or filesystem writes."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from autorouter import placement_copper as pc, pipeline as p, routing_scope as rs, sexpr as sx
from experiments.placement_native_proposal_v1 import contract as c, ordinary_fixture as fixture
from experiments.placement_native_proposal_v1 import multipad_fixture
from experiments.placement_native_proposal_v1.test_contract import fixture as old_fixture, moves as old_moves

REGION = [7_000_000, 7_000_000, 31_000_000, 13_000_000]


def raw(tree):
    return (sx.dump(tree) + '\n').encode()


def route(label, net, start=('12', '10.825'), end=('26', '9.175')):
    return ['segment', ['start', *start], ['end', *end], ['width', '0.2'],
            ['layer', '"F.Cu"'], ['net', json.dumps(net)],
            ['uuid', json.dumps(fixture.uid('copper-plan-' + label))]]


def source_tree(*, legacy=False):
    tree = fixture.board()
    tree.extend([route('A', 'ROUTE_A'), route('A-remote', 'ROUTE_A', ('10', '8'), ('11', '8')),
                 route('B', 'ROUTE_B', ('12', '9.175'), ('26', '10.825')),
                 route('unrelated', 'GND', ('12', '24'), ('26', '24'))])
    # This is a newly authored small fixture, never stripping an acquired board.
    sx.one(tree, 'zone').append(['filled_polygon', ['layer', '"B.Cu"'],
                                ['pts', ['xy', '8', '22'], ['xy', '9', '22'], ['xy', '9', '23']]])
    if legacy:
        nodes = [*p.routes(tree), *sx.children(tree, 'zone'),
                 *(pad for fp in sx.children(tree, 'footprint') for pad in sx.children(fp, 'pad'))]
        names = sorted({sx.unquote(sx.one(node, 'net')[1]) for node in nodes})
        codes = {name: str(i + 1) for i, name in enumerate(names)}
        tree[3:3] = [['net', '0', '""']] + [['net', codes[name], json.dumps(name)] for name in names]
        for node in nodes:
            field = sx.one(node, 'net'); name = sx.unquote(field[1])
            field[:] = ['net', codes[name], json.dumps(name)] if node[0] == 'pad' else ['net', codes[name]]
    return tree


def fp(tree, reference='J1'):
    return next(node for node in sx.children(tree, 'footprint') if fixture.base.reference(node) == reference)


class PlacementCopper(unittest.TestCase):
    def setUp(self):
        self.tree = source_tree()
        self.raw = raw(self.tree)
        self.selected = fixture.selected()
        self.moves = dict(zip(self.selected, ([14_000_000, 10_000_000], [24_000_000, 10_000_000])))
        self.options = dict(scope=c.ORDINARY_SCOPE, region_nm=REGION)
        self.plan = pc.propose(self.raw, self.selected)
        self.prepared = pc.prepare(self.raw, self.plan)
        self.posed = c.translated_tree(self.prepared, self.moves, selected=self.selected, **self.options)

    def refused(self, call, *args, **kwargs):
        with self.assertRaises((ValueError, p.Rejected)):
            call(*args, **kwargs)

    def test_modern_and_legacy_exact_partition_and_source_preserved(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                tree = source_tree(legacy=legacy); original = copy.deepcopy(tree); data = raw(tree)
                selected = self.selected.copy(); plan = pc.propose(data, selected)
                prepared = pc.prepare(data, plan)
                self.assertEqual(tree, original)
                self.assertEqual(raw(tree), data)
                self.assertEqual(plan, pc.propose(data, self.selected))
                self.assertEqual(plan['source_sha256'], hashlib.sha256(data).hexdigest())
                self.assertEqual(plan['source_scope'], c.ORDINARY_SCOPE)
                self.assertEqual(plan['incident_names'], ['ROUTE_A', 'ROUTE_B'])
                self.assertEqual(len(plan['removed_routes']), 3)
                self.assertEqual(len(plan['protected_routes']), 2)
                self.assertEqual(plan['original_route_count'], 5)
                self.assertEqual(prepared, raw(rs.task(tree, plan['incident_names'])))
                self.assertEqual(plan['routing_scope_binding'], rs.bind(data, plan['incident_names']))
                self.assertEqual(plan['task_sha256'], hashlib.sha256(prepared).hexdigest())
                self.assertEqual(p.immutable(sx.parse(prepared.decode())), p.immutable(tree))
                self.assertEqual(p.routes(sx.parse(prepared.decode())), [p.routes(tree)[0], p.routes(tree)[-1]])
                self.assertEqual(sx.children(sx.one(sx.parse(prepared.decode()), 'zone'), 'filled_polygon'), [])
                for record in plan['removed_routes'] + plan['protected_routes']:
                    self.assertIn(record['ast'], p.routes(tree))
                    self.assertEqual(record['record_sha256'], hashlib.sha256(sx.dump(record['ast']).encode()).hexdigest())
                self.assertEqual([row['reference'] for row in plan['selected_components']], ['J1', 'J2'])
                self.assertTrue(all(len(row['pads']) == 2 for row in plan['selected_components']))
                selected.reverse()
                self.assertEqual(plan['selected'], self.selected)

    def test_every_incident_route_is_removed_not_only_near_selected_parts(self):
        removed = {r['uuid'] for r in self.plan['removed_routes']}
        self.assertIn(fixture.uid('copper-plan-A-remote'), removed)
        self.assertEqual({r['net_name'] for r in self.plan['removed_routes']}, {'ROUTE_A', 'ROUTE_B'})
        self.assertEqual({r['net_name'] for r in self.plan['protected_routes']}, {'KEEP', 'GND'})

    def test_no_existing_incident_copper_still_has_explicit_plan_not_approval(self):
        source = raw(fixture.board()); plan = pc.propose(source, self.selected)
        self.assertEqual(plan['removed_routes'], [])
        self.assertEqual(plan['incident_names'], ['ROUTE_A', 'ROUTE_B'])
        self.assertEqual(plan['original_route_count'], 1)
        for field in ('approval_granted', 'execution_authorized', 'routing_accepted', 'native_validation_performed'):
            self.assertIs(plan[field], False)
        self.assertEqual(p.routes(sx.parse(pc.prepare(source, plan).decode())), p.routes(fixture.board()))

    def test_incident_locked_or_explicitly_protected_copper_refuses(self):
        for route_index in (1, 2, 3):
            tree = copy.deepcopy(self.tree); p.routes(tree)[route_index].append(['locked', 'yes'])
            with self.subTest(route_index=route_index):
                self.refused(pc.propose, raw(tree), self.selected)
        for name in ('ROUTE_A', 'ROUTE_B'):
            self.refused(pc.propose, self.raw, self.selected, protected_names=[name])
        for record in self.plan['removed_routes']:
            self.refused(pc.propose, self.raw, self.selected, protected_route_ids=[record['uuid']])
        # User-protected incident nets remain fixed even with no current route.
        self.refused(pc.propose, raw(fixture.board()), self.selected, protected_names=['ROUTE_A'])

    def test_unrelated_user_protections_are_bound_and_immutable(self):
        names = ['KEEP', 'GND']; identities = [row['uuid'] for row in self.plan['protected_routes']]
        plan = pc.propose(self.raw, self.selected, protected_names=names, protected_route_ids=identities)
        captured = copy.deepcopy(plan); names.clear(); identities.clear()
        self.assertEqual(plan, captured)
        self.assertEqual(pc.prepare(self.raw, plan), self.prepared)
        self.assertNotEqual(plan['plan_sha256'], self.plan['plan_sha256'])
        self.assertTrue(pc.audit_routed(self.raw, raw(self.posed), plan, self.moves, **self.options)['audit_passed'])

    def test_selection_protection_and_source_types_are_strict(self):
        for selected in (None, (), [], True, [True], [self.selected[0]] * 2, [self.selected[0].upper()],
                         ['00000000-0000-0000-0000-000000000000'], [fixture.uid('missing')], self.selected * 9):
            with self.subTest(selected=selected):self.refused(pc.propose, self.raw, selected)
        for value in ((), 'KEEP', True, [True], ['MISSING'], ['KEEP', 'KEEP'], [''], ['0']):
            with self.subTest(protected_names=value):self.refused(pc.propose, self.raw, self.selected, protected_names=value)
        for value in ((), 'id', True, [True], [fixture.uid('missing')], [self.selected[0]],
                      [self.plan['protected_routes'][0]['uuid']] * 2):
            with self.subTest(protected_route_ids=value):self.refused(pc.propose, self.raw, self.selected, protected_route_ids=value)
        for value in (None, b'', self.raw.decode(), self.raw * 100):
            with self.subTest(source_type=type(value).__name__):self.refused(pc.propose, value, self.selected)

    def test_locked_ineligible_or_unnamed_selected_parts_refuse(self):
        tree = copy.deepcopy(self.tree); fp(tree).append(['locked', 'yes'])
        self.refused(pc.propose, raw(tree), self.selected)
        self.refused(pc.propose, self.raw, [c.uid(fp(self.tree, 'J3'))])
        for mode in ('absent', 'empty', 'zero'):
            tree = copy.deepcopy(self.tree); pad = sx.children(fp(tree), 'pad')[0]; net = sx.one(pad, 'net')
            if mode == 'absent':pad.remove(net)
            else:net[1] = '""' if mode == 'empty' else '"0"'
            with self.subTest(mode=mode):self.refused(pc.propose, raw(tree), self.selected)

    def test_ambiguous_ids_and_net_mapping_refuse(self):
        for mode in ('fp_duplicate', 'pad_duplicate', 'route_duplicate', 'immutable_collision', 'net_duplicate', 'net_conflict', 'net_field_duplicate'):
            tree = source_tree(legacy=True)
            if mode == 'fp_duplicate':sx.one(fp(tree, 'J2'), 'uuid')[1] = sx.one(fp(tree), 'uuid')[1]
            elif mode == 'pad_duplicate':sx.one(sx.children(fp(tree), 'pad')[1], 'uuid')[1] = sx.one(sx.children(fp(tree), 'pad')[0], 'uuid')[1]
            elif mode == 'route_duplicate':tree.append(copy.deepcopy(p.routes(tree)[1]))
            elif mode == 'immutable_collision':sx.one(p.routes(tree)[1], 'uuid')[1] = sx.one(fp(tree), 'uuid')[1]
            elif mode == 'net_duplicate':tree.append(copy.deepcopy(sx.children(tree, 'net')[1]))
            elif mode == 'net_conflict':sx.one(sx.children(fp(tree), 'pad')[0], 'net')[2] = '"WRONG"'
            else:sx.children(fp(tree), 'pad')[0].append(copy.deepcopy(sx.one(sx.children(fp(tree), 'pad')[0], 'net')))
            with self.subTest(mode=mode):self.refused(pc.propose, raw(tree), self.selected)

    def test_unknown_unnamed_or_unsupported_source_copper_is_refused_not_removed(self):
        for mode in ('unknown', 'empty', 'absent', 'via', 'arc'):
            tree = copy.deepcopy(self.tree); item = p.routes(tree)[-1]
            if mode == 'unknown':sx.one(item, 'net')[1] = '"UNKNOWN"'
            elif mode == 'empty':sx.one(item, 'net')[1] = '""'
            elif mode == 'absent':item.remove(sx.one(item, 'net'))
            else:item[0] = mode
            before = raw(tree)
            with self.subTest(mode=mode):self.refused(pc.propose, before, self.selected)
            self.assertEqual(raw(tree), before)

    def test_source_change_including_whitespace_invalidates_plan(self):
        for mode in ('whitespace', 'route', 'net', 'lock', 'zone', 'setup', 'pose'):
            tree = copy.deepcopy(self.tree)
            if mode == 'route':sx.one(p.routes(tree)[1], 'end')[1] = '25'
            elif mode == 'net':sx.one(p.routes(tree)[1], 'net')[1] = '"ROUTE_B"'
            elif mode == 'lock':p.routes(tree)[1].append(['locked', 'yes'])
            elif mode == 'zone':sx.one(sx.one(sx.one(tree, 'zone'), 'polygon'), 'pts')[1][1] = '7.1'
            elif mode == 'setup':sx.one(tree, 'setup').append(['pad_to_paste_clearance', '0.1'])
            elif mode == 'pose':sx.one(fp(tree), 'at')[1] = '12.1'
            changed = self.raw + b'\n' if mode == 'whitespace' else raw(tree)
            with self.subTest(mode=mode):self.refused(pc.prepare, changed, self.plan)

    def test_plan_is_recomputed_not_trusted_by_hash_or_success_field(self):
        cases = []
        for mode in ('extra', 'authority', 'schema_bool', 'schema_float', 'hash', 'source_hash', 'selected',
                     'name', 'removed', 'protected', 'binding', 'tuple'):
            plan = copy.deepcopy(self.plan)
            if mode == 'extra':plan['shell'] = 'anything'
            elif mode == 'authority':plan['approval_granted'] = True
            elif mode == 'schema_bool':plan['schema'] = True
            elif mode == 'schema_float':plan['schema'] = 1.0
            elif mode == 'hash':plan['plan_sha256'] = '0' * 64
            elif mode == 'source_hash':plan['source_sha256'] = '0' * 64
            elif mode == 'selected':plan['selected'] = plan['selected'][::-1]
            elif mode == 'name':plan['selected_components'][0]['reference'] = 'WRONG'
            elif mode == 'removed':plan['removed_routes'][0]['ast'][1][1] = '99'
            elif mode == 'protected':plan['protected_routes'].clear()
            elif mode == 'binding':plan['routing_scope_binding']['protected_count'] = 0
            elif mode == 'tuple':plan['selected'] = tuple(plan['selected'])
            cases.append((mode, plan))
        cycle = {}; cycle['cycle'] = cycle; cases.append(('cycle', cycle))
        for mode, plan in cases:
            with self.subTest(mode=mode):self.refused(pc.prepare, self.raw, plan)
        self.refused(pc.prepare, self.raw, None)
        # Re-signing attacker-edited JSON is not approval or a source witness.
        forged = copy.deepcopy(self.plan)
        forged['protected_routes'].clear()
        forged['plan_sha256'] = hashlib.sha256(c.constraints.encoded({key: value for key, value in forged.items() if key != 'plan_sha256'})).hexdigest()
        self.refused(pc.prepare, self.raw, forged)

    def test_translation_allows_only_selected_xy_and_derived_fill(self):
        tree = copy.deepcopy(self.posed)
        sx.one(tree, 'zone').append(['filled_polygon', ['layer', '"B.Cu"'], ['pts', ['xy', '8', '22'], ['xy', '10', '22'], ['xy', '10', '23']]])
        proof = pc.audit_translation(self.raw, raw(tree), self.plan, self.moves, **self.options)
        self.assertTrue(proof['audit_passed'])
        self.assertTrue(proof['translation']['exact_immutable_AST'])
        self.assertIs(proof['native_validation_performed'], False)
        self.assertIs(proof['routing_accepted'], False)
        self.assertEqual(proof['moves_nm'], self.moves)
        self.assertEqual(sx.one(fp(tree), 'at')[3], '90')
        self.assertEqual(sx.one(fp(tree, 'J2'), 'at')[3], '270')
        self.assertEqual(raw(self.tree), self.raw)
        tree.append(route('new', 'ROUTE_A'))
        self.refused(pc.audit_translation, self.raw, raw(tree), self.plan, self.moves, **self.options)

    def test_translation_and_routing_reject_any_nonallowed_original_change(self):
        for mode in ('fixed_pose', 'selected_angle', 'selected_side', 'pad_size', 'pad_net', 'pad_id', 'zone', 'zone_fill_rule', 'setup', 'edge', 'protected_delete', 'protected_width', 'protected_net', 'protected_lock'):
            tree = copy.deepcopy(self.posed)
            if mode == 'fixed_pose':sx.one(fp(tree, 'J5'), 'at')[1] = '11'
            elif mode == 'selected_angle':sx.one(fp(tree), 'at')[3] = '180'
            elif mode == 'selected_side':sx.one(fp(tree), 'layer')[1] = '"B.Cu"'
            elif mode == 'pad_size':sx.one(sx.children(fp(tree), 'pad')[0], 'size')[1] = '0.7'
            elif mode == 'pad_net':sx.one(sx.children(fp(tree), 'pad')[0], 'net')[1] = '"GND"'
            elif mode == 'pad_id':sx.one(sx.children(fp(tree), 'pad')[0], 'uuid')[1] = json.dumps(fixture.uid('new-pad'))
            elif mode == 'zone':sx.one(sx.one(sx.one(tree, 'zone'), 'polygon'), 'pts')[1][1] = '7.1'
            elif mode == 'zone_fill_rule':sx.one(sx.one(tree, 'zone'), 'fill').append(['thermal_gap', '0'])
            elif mode == 'setup':sx.one(tree, 'setup').append(['pad_to_paste_clearance', '0.1'])
            elif mode == 'edge':sx.one(sx.children(tree, 'gr_rect')[0], 'end')[1] = '33'
            elif mode == 'protected_delete':tree.remove(p.routes(tree)[0])
            elif mode == 'protected_width':sx.one(p.routes(tree)[0], 'width')[1] = '0.4'
            elif mode == 'protected_net':sx.one(p.routes(tree)[0], 'net')[1] = '"ROUTE_A"'
            elif mode == 'protected_lock':p.routes(tree)[0].remove(sx.one(p.routes(tree)[0], 'locked'))
            for checker in (pc.audit_translation, pc.audit_routed):
                with self.subTest(mode=mode, checker=checker.__name__):self.refused(checker, self.raw, raw(tree), self.plan, self.moves, **self.options)

    def test_wrong_missing_or_unsafe_moves_regions_and_scopes_refuse(self):
        for mode in ('missing', 'extra', 'bool', 'float', 'outside', 'overlap', 'wrong_pose', 'preserved_copper_region', 'zone_region', 'scope'):
            moves = copy.deepcopy(self.moves); options = copy.deepcopy(self.options)
            if mode == 'missing':moves.pop(self.selected[1])
            elif mode == 'extra':moves[c.uid(fp(self.tree, 'J5'))] = [12_000_000, 24_000_000]
            elif mode == 'bool':moves[self.selected[0]][0] = True
            elif mode == 'float':moves[self.selected[0]][0] = 14e6
            elif mode == 'outside':moves[self.selected[0]][0] = 99_000_000
            elif mode == 'overlap':moves[self.selected[0]] = moves[self.selected[1]].copy()
            elif mode == 'wrong_pose':moves[self.selected[0]][0] = 15_000_000
            elif mode == 'preserved_copper_region':options['region_nm'][3] = 17_000_000
            elif mode == 'zone_region':options['region_nm'][3] = 25_000_000
            elif mode == 'scope':options['scope'] = c.MULTIPAD_SCOPE
            for checker in (pc.audit_translation, pc.audit_routed):
                with self.subTest(mode=mode, checker=checker.__name__):self.refused(checker, self.raw, raw(self.posed), self.plan, moves, **options)

    def test_routed_scope_reuses_shared_checker_and_never_proves_completion(self):
        for legacy in (False, True):
            source = raw(source_tree(legacy=legacy)); plan = pc.propose(source, self.selected)
            posed = c.translated_tree(pc.prepare(source, plan), self.moves, selected=self.selected, **self.options)
            added = route('routed-A', 'ROUTE_A')
            if legacy:
                code = next(node[1] for node in sx.children(posed, 'net') if sx.unquote(node[2]) == 'ROUTE_A')
                sx.one(added, 'net')[1:] = [code]
            posed.append(added)
            with self.subTest(legacy=legacy), patch.object(rs, 'audit', wraps=rs.audit) as shared:
                proof = pc.audit_routed(source, raw(posed), plan, self.moves, **self.options)
                self.assertEqual(shared.call_count, 1)
                self.assertTrue(proof['audit_passed'])
                self.assertEqual(proof['routing_scope']['selected_route_count'], 1)
                self.assertIs(proof['routing_scope']['routing_accepted'], False)
                self.assertIs(proof['native_validation_performed'], False)
            # Missing selected routes are scope-valid, deliberately NOT completion.
            posed.remove(added)
            proof = pc.audit_routed(source, raw(posed), plan, self.moves, **self.options)
            self.assertEqual(proof['routing_scope']['selected_route_count'], 0)
            self.assertFalse(proof['routing_accepted'])

    def test_generated_route_net_lock_or_uuid_escape_refuses(self):
        for mode in ('unrelated', 'unknown', 'empty', 'lock', 'pad_collision', 'protected_collision', 'duplicate'):
            tree = copy.deepcopy(self.posed); added = route('new', 'ROUTE_A'); tree.append(added)
            if mode in ('unrelated', 'unknown', 'empty'):sx.one(added, 'net')[1] = json.dumps({'unrelated':'GND','unknown':'UNKNOWN','empty':''}[mode])
            elif mode == 'lock':added.append(['locked', 'yes'])
            elif mode == 'pad_collision':sx.one(added, 'uuid')[1] = sx.one(sx.children(fp(tree), 'pad')[0], 'uuid')[1]
            elif mode == 'protected_collision':sx.one(added, 'uuid')[1] = sx.one(p.routes(tree)[0], 'uuid')[1]
            elif mode == 'duplicate':tree.append(copy.deepcopy(added))
            with self.subTest(mode=mode):self.refused(pc.audit_routed, self.raw, raw(tree), self.plan, self.moves, **self.options)

    def test_original_api_scopes_and_default_preserve_policy_remain_unchanged(self):
        # Default and multipad contracts still reject tracked selection until the
        # caller deliberately opts into this separate affected-copper plan.
        source = old_fixture(); tree = c.read_board(source)
        original_plan = pc.propose(source, list(c.SELECTED))
        prepared = pc.prepare(source, original_plan)
        candidate = raw(c.translated_tree(prepared, old_moves()))
        self.assertTrue(pc.audit_translation(source, candidate, original_plan, old_moves(), scope=c.DEFAULT_SCOPE, region_nm=c.REGION_NM)['audit_passed'])
        multi = multipad_fixture.board(); selected = [multipad_fixture.uid(ref+'-footprint') for ref in ('J1','J2')]
        multi.append(route('multi-A', 'ROUTE_A'))
        data = raw(multi); observation = c.inspect_board(data, scope=c.MULTIPAD_SCOPE)
        moves = dict(zip(selected, ([14_000_000,10_000_000],[24_000_000,10_000_000])))
        self.refused(c.validate_moves, observation, moves, scope=c.MULTIPAD_SCOPE, selected=selected, region_nm=REGION)
        plan = pc.propose(data, selected); prepared = pc.prepare(data, plan)
        candidate = raw(c.translated_tree(prepared, moves, scope=c.MULTIPAD_SCOPE, selected=selected, region_nm=REGION))
        self.assertTrue(pc.audit_translation(data, candidate, plan, moves, scope=c.MULTIPAD_SCOPE, region_nm=REGION)['audit_passed'])
        self.refused(c.validate_moves, c.inspect_board(self.raw, scope=c.ORDINARY_SCOPE), self.moves, selected=self.selected, **self.options)

    def test_all_pure_operations_preserve_caller_data_and_never_start_processes(self):
        original_plan = copy.deepcopy(self.plan); original_moves = copy.deepcopy(self.moves)
        with patch('subprocess.Popen', side_effect=AssertionError('Pure copper planning may not run tools')):
            plan = pc.propose(self.raw, self.selected)
            self.assertEqual(pc.prepare(self.raw, plan), self.prepared)
            pc.audit_translation(self.raw, raw(self.posed), plan, self.moves, **self.options)
            pc.audit_routed(self.raw, raw(self.posed), plan, self.moves, **self.options)
        self.assertEqual(self.plan, original_plan)
        self.assertEqual(self.moves, original_moves)
        self.assertEqual(raw(self.tree), self.raw)


if __name__ == '__main__':
    unittest.main()
