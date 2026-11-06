"""Small pure AST/constraint controls; no Native import, fixture writes or claims."""
import copy
import hashlib
import unittest
import uuid
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from experiments.placement_native_proposal_v1 import contract as c


def identity(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'placement-native-probe-pure:' + name))


def raw(tree):
    return (c.sx.dump(tree) + '\n').encode()


def fixture():
    parts = []
    for index, (fid, x, y) in enumerate((*zip(c.SELECTED, (12, 26), (10, 10)), (identity('anchor'), 12, 20))):
        parts.append(f'''(footprint "pure" (layer "F.Cu") (uuid "{fid}") (at {x} {y})
            (property "Reference" "J{index}" (at 0 0) (layer "F.Fab"))
            (attr through_hole)
            (fp_rect (start -1.25 -1.25) (end 1.25 1.25)
                (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd")
                (uuid "{identity('court' + str(index))}"))
            (pad "1" thru_hole circle (at 0 0) (size 2 2) (drill 0.8)
                (layers "*.Cu" "*.Mask") (net 1 "signal") (uuid "{identity('pad' + str(index))}")))''')
    return f'''(kicad_pcb (version 20241229) (generator "pure_fixture")
        (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) (net 1 "signal")
        {''.join(parts)}
        (gr_rect (start 6 6) (end 32 30) (stroke (width 0.05) (type default))
            (fill none) (layer "Edge.Cuts") (uuid "{identity('edge')}"))
        (zone (net 1) (layer "B.Cu") (uuid "{identity('zone')}")
            (hatch edge 0.5) (connect_pads yes (clearance 0.3)) (min_thickness 0.25)
            (filled_areas_thickness no) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
            (polygon (pts (xy 7 23) (xy 31 23) (xy 31 29) (xy 7 29))) (net_name "signal")))'''.encode()


def moves():
    return dict(zip(c.SELECTED, ([14_000_000, 10_000_000], [24_000_000, 10_000_000])))


class NativeProposalPureContract(unittest.TestCase):
    def setUp(self):
        self.source = fixture()
        self.observation = c.inspect_board(self.source)

    def test_application_policy_defaults_to_native_and_requires_explicit_source_choice(self):
        from . import driver
        self.assertEqual(c.application_policy(), 'native-save-v1')
        self.assertEqual(c.application_policy('source-translation-v1'), 'source-translation-v1')
        for invalid in (None, True, 'native', 'source-translation', ''):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                c.application_policy(invalid)
        argv=['--runtime','unused-runtime','--protocol','unused-protocol']
        with patch.object(driver,'prepare') as prepare:
            self.assertEqual(driver.main(argv),0)
            self.assertEqual(prepare.call_args.args[-1],'native-save-v1')
            self.assertEqual(driver.main(argv+['--application-policy','source-translation-v1']),0)
            self.assertEqual(prepare.call_args.args[-1],'source-translation-v1')

    def refill_fixture(self):
        preimage=raw(c.translated_tree(self.source,moves()))
        refilled=c.read_board(preimage)
        c.sx.one(refilled,'version')[1]='20260206'
        c.sx.one(refilled,'generator')[1]='"synthetic-normalized-copy"'
        refilled[:]=[n for n in refilled if not (type(n) is list and n and n[0]=='net')]
        for fp in c.sx.children(refilled,'footprint'):
            c.sx.one(c.sx.one(fp,'pad'),'net')[:]=['net','"signal"']
        zone=c.sx.one(refilled,'zone');c.sx.one(zone,'net')[:]=['net','"signal"']
        zone.append(['filled_polygon',['layer','"B.Cu"'],['pts',['xy','7','23'],['xy','8','23'],['xy','8','24']]])
        return preimage,raw(refilled)

    def test_separate_refill_transfers_only_fill_and_does_not_relax_strict_policy(self):
        preimage,refilled=self.refill_fixture();before=(preimage[:],refilled[:])
        with self.assertRaisesRegex(ValueError,'beyond selected'):
            c.check_translation(self.source,refilled,moves())
        candidate=c.transplant_refill(preimage,refilled)
        self.assertEqual((preimage,refilled),before)
        self.assertEqual(c.p._without_derived_fill(c.read_board(candidate)),c.read_board(preimage))
        self.assertEqual(c.sx.one(c.read_board(candidate),'version'),['version','20241229'])
        self.assertEqual(len(c.sx.children(c.sx.one(c.read_board(candidate),'zone'),'filled_polygon')),1)
        self.assertTrue(c.check_translation(self.source,candidate,moves())['exact_immutable_AST'])
        audit=c.check_refill_reconstruction(preimage,refilled,candidate)
        self.assertEqual(audit['native_output_sha256'],hashlib.sha256(refilled).hexdigest())
        self.assertTrue(audit['exact_reconstruction'])

    def test_refill_reconstruction_rejects_stale_preimage_native_fill_or_candidate(self):
        preimage,refilled=self.refill_fixture();candidate=c.transplant_refill(preimage,refilled)
        stale=c.read_board(preimage);c.sx.one(stale,'generator')[1]='"changed"'
        changed=c.read_board(refilled);c.sx.one(c.sx.one(c.sx.one(changed,'zone'),'filled_polygon'),'pts')[1][1]='7.1'
        for a,b,d in ((raw(stale),refilled,candidate),(preimage,raw(changed),candidate),
                      (preimage,refilled,candidate+b' ')):
            with self.subTest(a=a[:30],b=b[:30]),self.assertRaisesRegex(ValueError,'exact retained refill'):
                c.check_refill_reconstruction(a,b,d)

    def test_refill_zone_identity_loss_duplication_or_extra_zone_is_refused(self):
        preimage,refilled=self.refill_fixture()
        for mode in ('missing','duplicate','extra'):
            tree=c.read_board(refilled);zone=c.sx.one(tree,'zone')
            if mode=='missing':tree.remove(zone)
            else:
                extra=copy.deepcopy(zone)
                if mode=='extra':c.sx.one(extra,'uuid')[1]='"'+identity('extra-zone')+'"'
                tree.append(extra)
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'zone identities'):
                c.transplant_refill(preimage,raw(tree))

    def test_route_derivation_only_strips_routes_and_preserves_source(self):
        tree = c.read_board(self.source)
        tree.append(c.sx.parse(f'(segment (start 12 10) (end 26 10) (width 0.3) (layer "F.Cu") (net 1) (uuid "{identity("track")}") (locked yes))'))
        protected_source = raw(tree); before = protected_source[:]
        derived, manifest = c.derive_unrouted(protected_source)
        self.assertEqual(protected_source, before)
        self.assertEqual(c.read_board(derived), c.read_board(self.source))
        self.assertEqual(manifest['removed_routes'][0]['locked'], True)
        self.assertEqual(manifest['original_board_sha256'], hashlib.sha256(before).hexdigest())
        self.assertIs(manifest['original_mutated'], False)
        self.assertIs(manifest['all_other_AST_fields_identical'], True)

    def test_uuid_identity_is_independent_of_duplicate_reference_labels(self):
        tree = c.read_board(self.source)
        for fp in c.sx.children(tree, 'footprint'):
            c.sx.one(fp, 'property')[2] = '"DUPLICATE"'
        observation = c.inspect_board(raw(tree))
        self.assertEqual(len({row['uuid'] for row in observation['footprints']}), 3)
        self.assertEqual(len({row['reference'] for row in observation['footprints']}), 1)
        self.assertEqual(len(c.facts_from_observation(observation)['components']), 3)

    def test_selected_translations_are_valid_and_integer_tens_survive(self):
        candidate = raw(c.translated_tree(self.source, moves()))
        result = c.check_translation(self.source, candidate, moves())
        self.assertIs(result['exact_immutable_AST'], True)
        positions = {row['uuid']: row['position_nm'] for row in c.inspect_board(candidate)['footprints']}
        for fid, xy in moves().items():
            self.assertEqual(positions[fid], xy)
        target = moves(); target[c.SELECTED[0]] = [10_000_000, 10_000_000]
        self.assertIn(['at', '10', '10'], c.sx.children(c.translated_tree(self.source, target), 'footprint')[0])

    def test_quantization_revalidates_source_and_leaves_input_unchanged(self):
        facts = c.facts_from_observation(self.observation)
        candidate = c.constraints.original_alternative(facts)
        row = next(row for row in candidate['transforms'] if row['component_id'] == c.SELECTED[0])
        row['x_mm'] = 14.00000049
        before = copy.deepcopy(candidate)
        quantized, integer_moves = c.quantized_translation(facts, candidate)
        self.assertEqual(candidate, before)
        self.assertEqual(integer_moves[c.SELECTED[0]], [14_000_000, 10_000_000])
        self.assertEqual(c.validate_moves(self.observation, integer_moves), quantized)
        candidate['source_sha256'] = '0' * 64
        with self.assertRaises(c.constraints.Refused):
            c.quantized_translation(facts, candidate)

    def test_unselected_unknown_and_partial_move_maps_are_refused(self):
        for invalid in ({c.SELECTED[0]: [14_000_000, 10_000_000]},
                        {**moves(), identity('anchor'): [20_000_000, 20_000_000]},
                        {**moves(), identity('unknown'): [20_000_000, 20_000_000]}):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'selected UUIDs'):
                c.check_translation(self.source, self.source, invalid)

    def test_bounds_region_overlap_and_noninteger_translation_refused(self):
        for xy in ([40_000_000, 10_000_000], [14_000_000, 16_000_000], [24_000_000, 10_000_000], [True, 10_000_000]):
            invalid = moves(); invalid[c.SELECTED[0]] = xy
            with self.subTest(xy=xy), self.assertRaises(ValueError):
                c.validate_moves(self.observation, invalid)

    def test_locked_selected_component_cannot_move(self):
        tree = c.read_board(self.source); c.sx.children(tree, 'footprint')[0].append(['locked', 'yes'])
        locked = raw(tree)
        with self.assertRaises(ValueError):
            c.validate_moves(c.inspect_board(locked), moves())
        with self.assertRaisesRegex(ValueError, 'Locked'):
            c.translated_tree(locked, moves())

    def test_every_nontranslation_field_remains_authoritative(self):
        def fp(tree):return c.sx.children(tree, 'footprint')[0]
        def pad(tree):return c.sx.one(fp(tree), 'pad')
        def change_net(tree):c.sx.one(pad(tree), 'net')[2] = '"other"'
        def change_pad_uuid(tree):c.sx.one(pad(tree), 'uuid')[1] = '"' + identity('changed') + '"'
        def change_pad_size(tree):c.sx.one(pad(tree), 'size')[1] = '1.9'
        def change_side(tree):c.sx.one(fp(tree), 'layer')[1] = '"B.Cu"'
        def change_angle(tree):c.sx.one(fp(tree), 'at').append('90')
        def change_field(tree):c.sx.one(fp(tree), 'property')[2] = '"DIFFERENT"'
        def change_edge(tree):c.sx.one(c.sx.one(tree, 'gr_rect'), 'end')[1] = '33'
        def change_zone(tree):c.sx.one(c.sx.one(tree, 'zone'), 'min_thickness')[1] = '0.2'
        def change_unselected(tree):c.sx.one(c.sx.children(tree, 'footprint')[2], 'at')[1] = '14'
        def add_copper(tree):tree.append(['segment', ['start', '14', '10'], ['end', '24', '10']])
        for change in (change_net, change_pad_uuid, change_pad_size, change_side, change_angle,
                       change_field, change_edge, change_zone, change_unselected, add_copper):
            tree = c.translated_tree(self.source, moves()); change(tree)
            with self.subTest(change=change.__name__), self.assertRaisesRegex(ValueError, 'beyond selected'):
                c.check_translation(self.source, raw(tree), moves())

    def test_derived_top_level_fill_only_is_exempt(self):
        tree = c.translated_tree(self.source, moves())
        c.sx.one(tree, 'zone').append(['filled_polygon', ['layer', '"B.Cu"'], ['pts', ['xy', '7', '23'], ['xy', '8', '23'], ['xy', '8', '24']]])
        self.assertTrue(c.check_translation(self.source, raw(tree), moves())['exact_immutable_AST'])
        c.sx.children(tree, 'footprint')[0].append(['filled_polygon', ['pts', ['xy', '1', '1']]])
        with self.assertRaises(ValueError):
            c.check_translation(self.source, raw(tree), moves())

    def test_ordinary_zone_keeps_inactive_native_defaults_without_admitting_rules(self):
        expected = self.observation['zones'][0]
        observed = dict(copy.deepcopy(expected), placement_enabled=False,
            placement_source_type='SHEETNAME', placement_source='',
            disallow=dict(tracks=True,vias=True,pads=True,copperpour=False,footprints=False))
        before = copy.deepcopy(observed)
        self.assertEqual(c.check_ordinary_zone(expected,observed),before)
        self.assertEqual(observed,before)
        for key,value in (('is_rule_area',True),('placement_enabled',True),
                          ('is_rule_area',0),('outlines_nm',[[[0,0],[1,0],[1,1]]])):
            changed=copy.deepcopy(observed);changed[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                c.check_ordinary_zone(expected,changed)
        changed=copy.deepcopy(observed);changed['disallow']['tracks']=1
        with self.assertRaises(ValueError):c.check_ordinary_zone(expected,changed)
        changed=copy.deepcopy(observed);del changed['disallow']['tracks']
        with self.assertRaises(ValueError):c.check_ordinary_zone(expected,changed)

    def test_unsupported_geometry_is_explicitly_refused(self):
        def extra_outline(tree):tree.append(copy.deepcopy(c.sx.one(tree, 'gr_rect')))
        def group(tree):tree.append(['group', '"unsupported"'])
        def rotated(tree):c.sx.one(c.sx.children(tree, 'footprint')[0], 'at').append('90')
        def custom_pad(tree):c.sx.one(c.sx.children(tree, 'footprint')[0], 'pad')[3] = 'custom'
        def pad_extension(tree):c.sx.one(c.sx.children(tree, 'footprint')[0], 'pad').append(['padstack', ['mode', 'custom']])
        def offcentre_pad(tree):c.sx.one(c.sx.one(c.sx.children(tree, 'footprint')[0], 'pad'), 'at')[1] = '0.1'
        def rule_area(tree):c.sx.one(tree, 'zone').append(['keepout', ['tracks', 'not_allowed']])
        for change in (extra_outline, group, rotated, custom_pad, pad_extension, offcentre_pad, rule_area):
            tree = c.read_board(self.source); change(tree)
            with self.subTest(change=change.__name__), self.assertRaises(ValueError):
                c.inspect_board(raw(tree))


class CompletedWorkerFreshness(unittest.TestCase):
    def test_native_layer_identity_does_not_depend_on_display_spelling(self):
        from .worker import exact_native_layer
        for display in ('F.CrtYd', 'F.Courtyard', 'custom display name'):
            courtyard = SimpleNamespace(GetLayer=lambda:31, GetLayerName=lambda:display)
            self.assertTrue(exact_native_layer(courtyard,31))
            self.assertFalse(exact_native_layer(courtyard,29))
        for invalid in (True,'31',31.0):
            self.assertFalse(exact_native_layer(SimpleNamespace(GetLayer=lambda:invalid),31))

    def test_late_runtime_wrapper_or_tool_change_refuses_completed_worker(self):
        from .driver import runtime_unchanged
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            manifest = runtime / 'runtime-distribution.json'
            wrapper = runtime / 'pcbnew.py'
            manifest.write_bytes(b'original runtime'); wrapper.write_bytes(b'original wrapper')
            sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            spec = dict(runtime_manifest_sha256=sha(manifest), wrapper_sha256=sha(wrapper))
            tools = {'native': 'pinned native digest'}
            operations = SimpleNamespace(sha=sha, tool_manifest=lambda: dict(tools))
            self.assertTrue(runtime_unchanged(runtime,wrapper,spec,tools,operations))
            for target in (manifest,wrapper):
                original = target.read_bytes(); target.write_bytes(b'changed after worker exit')
                self.assertFalse(runtime_unchanged(runtime,wrapper,spec,tools,operations))
                target.write_bytes(original)
            operations.tool_manifest = lambda: {'native': 'changed after worker exit'}
            self.assertFalse(runtime_unchanged(runtime,wrapper,spec,tools,operations))
            def changed_during_read():
                wrapper.write_bytes(b'changed during tool read')
                return dict(tools)
            operations.tool_manifest = changed_during_read
            self.assertFalse(runtime_unchanged(runtime,wrapper,spec,tools,operations))


class MultipadPreservedContract(unittest.TestCase):
    def setUp(self):
        from . import multipad_fixture as fixture_module
        self.fixture = fixture_module
        self.source = raw(fixture_module.board())
        self.options = dict(scope=c.MULTIPAD_SCOPE,
            selected=[fixture_module.uid(ref+'-footprint') for ref in ('J1','J2')],
            region_nm=list(c.REGION_NM))
        self.observation = c.inspect_board(self.source,scope=c.MULTIPAD_SCOPE)
        self.moves = dict(zip(self.options['selected'],([14_000_000,10_000_000],[24_000_000,10_000_000])))

    def test_multiple_offsets_are_exact_sorted_and_copper_is_not_removed(self):
        self.assertEqual(len(self.observation['footprints']),6)
        self.assertEqual(sum(len(row['pads']) for row in self.observation['footprints']),8)
        self.assertEqual(self.observation['route_count'],1)
        self.assertEqual(self.observation['routes'][0]['uuid'],self.fixture.uid('protected-keep-track'))
        self.assertIs(self.observation['routes'][0]['locked'],True)
        for row in self.observation['footprints']:
            self.assertEqual([p['uuid'] for p in row['pads']],sorted(p['uuid'] for p in row['pads']))
            for pad in row['pads']:
                self.assertEqual(pad['position_nm'],[row['position_nm'][i]+pad['offset_nm'][i] for i in range(2)])
        facts=c.facts_from_observation(self.observation,**self.options)
        selected=[row for row in facts['components'] if row['id'] in self.options['selected']]
        self.assertEqual({tuple(p['offset_mm']) for row in selected for p in row['pads']},{(-1.27,0.0),(1.27,0.0)})
        candidate=raw(c.translated_tree(self.source,self.moves,**self.options))
        self.assertTrue(c.check_translation(self.source,candidate,self.moves,**self.options)['exact_immutable_AST'])
        self.assertEqual(c.p.routes(c.read_board(candidate)),c.p.routes(c.read_board(self.source)))
        with self.assertRaises(ValueError):c.inspect_board(self.source)  # Old scope is unchanged.

    def test_new_scope_requires_complete_explicit_selection_and_region(self):
        from .worker import request_scope
        self.assertEqual(request_scope({},c)['scope'],c.DEFAULT_SCOPE)
        request=dict(placement_scope=c.MULTIPAD_SCOPE,selected_footprints=self.options['selected'],allowed_region_nm=self.options['region_nm'])
        self.assertEqual(request_scope(request,c),self.options)
        for key in request:
            changed=dict(request);del changed[key]
            with self.subTest(missing=key),self.assertRaises(ValueError):request_scope(changed,c)
        with self.assertRaises(ValueError):c.facts_from_observation(self.observation,scope=c.MULTIPAD_SCOPE)
        for change in (dict(selected=[self.options['selected'][0]]*2),dict(selected=[identity('absent')]),
                       dict(region_nm=[True,7_000_000,31_000_000,13_000_000]),dict(region_nm=[7,7,7,13])):
            with self.subTest(change=change),self.assertRaises(ValueError):
                c.facts_from_observation(self.observation,**{**self.options,**change})

    def test_preserved_route_region_guard_counts_width_and_clearance(self):
        # KEEP at y16mm, width0.3mm, plus the explicit0.3mm proxy gap.
        options={**self.options,'region_nm':[7_000_000,7_000_000,31_000_000,15_550_000]}
        with self.assertRaisesRegex(ValueError,'clearance-expanded'):
            c.facts_from_observation(self.observation,**options)
        options['region_nm'][-1]-=1
        self.assertTrue(c.facts_from_observation(self.observation,**options)['tracks'])

    def test_component_on_tracked_net_is_fixed_without_invented_endpoint_incidence(self):
        tree=c.read_board(self.source)
        fp=next(row for row in c.sx.children(tree,'footprint') if c.uid(row)==self.options['selected'][0])
        c.sx.one(c.sx.children(fp,'pad')[0],'net')[1:] = ['"KEEP"']
        observation=c.inspect_board(raw(tree),scope=c.MULTIPAD_SCOPE)
        facts=c.facts_from_observation(observation,**self.options)
        self.assertIn(self.options['selected'][0],c.constraints.immovable(facts))
        with self.assertRaisesRegex(ValueError,'tracked component moved'):
            c.validate_moves(observation,self.moves,**self.options)

    def test_pad_extent_number_uuid_and_preserved_copper_tampering_refused(self):
        for change in ('extent','duplicate-number','duplicate-uuid'):
            tree=c.read_board(self.source);fp=next(row for row in c.sx.children(tree,'footprint') if c.uid(row)==self.options['selected'][0]);pads=c.sx.children(fp,'pad')
            if change=='extent':c.sx.one(pads[0],'at')[1]='2.7'
            elif change=='duplicate-number':pads[1][1]=pads[0][1]
            else:c.sx.one(pads[1],'uuid')[1]=c.sx.one(pads[0],'uuid')[1]
            with self.subTest(change=change),self.assertRaises(ValueError):c.inspect_board(raw(tree),scope=c.MULTIPAD_SCOPE)
        candidate=c.translated_tree(self.source,self.moves,**self.options)
        c.sx.one(c.sx.one(candidate,'segment'),'end')[1]='26.000001'
        with self.assertRaisesRegex(ValueError,'beyond selected'):
            c.check_translation(self.source,raw(candidate),self.moves,**self.options)

    def test_vias_arcs_and_unwitnessed_segments_are_explicitly_unsupported(self):
        for change in ('via','arc','orphan-net'):
            tree=c.read_board(self.source);route=c.sx.one(tree,'segment')
            if change=='orphan-net':c.sx.one(route,'net')[1:] = ['"ORPHAN"']
            else:route[0]=change
            with self.subTest(change=change),self.assertRaises(ValueError):c.inspect_board(raw(tree),scope=c.MULTIPAD_SCOPE)


if __name__ == '__main__':
    unittest.main()
