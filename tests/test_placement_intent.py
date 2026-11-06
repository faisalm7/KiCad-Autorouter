"""Actual small owned saved projects and pure search; no Native or GUI claims."""
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
import uuid
from unittest.mock import patch

from autorouter import placement_intent as intent
from autorouter import gui, pipeline as pipeline, sexpr as sx
from experiments.placement_native_proposal_v1 import contract, multipad_fixture, ordinary_fixture
from experiments.constrained_placement_v1 import constraints


class PlacementIntentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='placement-intent-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.board = multipad_fixture.write_project(self.root / 'saved project')
        self.selected = [multipad_fixture.uid(ref + '-footprint') for ref in ('J1', 'J2')]
        self.region = [7_000_000, 7_000_000, 31_000_000, 13_000_000]
        self.options = intent.settings(self.selected, self.region)
        self.inspection = intent.inspect_saved(self.board)
        self.original = gui.source_inventory(self.board)

    def rewrite(self, change):
        tree = sx.read(self.board); change(tree)
        self.board.write_text(sx.dump(tree) + '\n')

    def proposal(self):
        proposal = intent.propose(self.inspection, self.options)
        self.assertEqual(proposal['search']['status'], 'proposals_ready')
        return proposal

    def review(self):
        # Review-state tests use a deterministic real, constraint-validated pose.
        # Dedicated search/cancellation tests above still execute the proposer;
        # an unrelated wall-clock search deadline must not gate draft checks.
        moves = dict(zip(self.selected, ([14_000_000, 10_000_000], [20_000_000, 10_000_000])))
        candidate = contract.validate_moves(self.inspection['observation'], moves,
            scope=contract.MULTIPAD_SCOPE, selected=self.selected, region_nm=self.region)
        return intent.Review(dict(kind='autorouter.placement-proposals.v1',
            inspection=copy.deepcopy(self.inspection), settings=copy.deepcopy(self.options),
            search=dict(status='proposals_ready', alternatives=[dict(candidate=candidate)])))

    def test_actual_saved_facts_report_fixed_reasons_and_no_validation_authority(self):
        with patch('subprocess.Popen', side_effect=AssertionError('pure inspection must not execute')):
            result = intent.inspect_saved(self.board)
        self.assertEqual(result['source_hashes'], self.original)
        by_ref = {row['reference']: row for row in result['components']}
        self.assertEqual(len(by_ref), 6)
        self.assertEqual(sum(row['pad_count'] for row in by_ref.values()), 8)
        self.assertFalse(by_ref['J1']['fixed_reasons']); self.assertFalse(by_ref['J2']['fixed_reasons'])
        self.assertIn('Shares a net with existing copper', by_ref['J3']['fixed_reasons'])
        self.assertIn('Shares a net with existing copper', by_ref['J4']['fixed_reasons'])
        self.assertEqual(result['observation']['route_count'], 1)
        self.assertTrue(result['observation']['routes'][0]['locked'])
        for field in ('native_validation_performed', 'execution_authorized', 'approval_granted'):
            self.assertIs(result[field], False)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_selected_ids_and_region_come_from_actual_request_not_fixture_defaults(self):
        custom = [str(uuid.uuid4()), str(uuid.uuid4())]
        def replace(tree):
            for fp in sx.children(tree, 'footprint'):
                identity = sx.unquote(sx.one(fp, 'uuid')[1])
                if identity in self.selected:
                    sx.one(fp, 'uuid')[1] = json.dumps(custom[self.selected.index(identity)])
        self.rewrite(replace)
        inspection = intent.inspect_saved(self.board)
        chosen = intent.settings(custom, [8_000_000, 8_000_000, 30_000_000, 12_000_000])
        facts = intent.facts(inspection, chosen)
        self.assertEqual(facts['selected'], custom)
        self.assertEqual([row['allowed_region_mm'] for row in facts['components'] if row['id'] in custom],
                         [[8., 8., 30., 12.]] * 2)
        with self.assertRaisesRegex(ValueError, 'Selected stable UUID absent'):
            intent.facts(inspection, self.options)

    def test_locked_and_routed_selection_refuse_without_changing_source(self):
        def lock(tree): sx.children(tree, 'footprint')[0].append(['locked', 'yes'])
        self.rewrite(lock); inspection = intent.inspect_saved(self.board)
        locked = next(row for row in inspection['components'] if row['uuid'] == self.selected[0])
        self.assertIn('Locked in KiCad', locked['fixed_reasons'])
        before = gui.source_inventory(self.board)
        with self.assertRaisesRegex(ValueError, 'locked or routed-net'):
            intent.facts(inspection, self.options)
        tracked = [multipad_fixture.uid(ref + '-footprint') for ref in ('J3', 'J4')]
        with self.assertRaises(ValueError):
            intent.facts(inspection, intent.settings(tracked, [7_000_000, 17_000_000, 31_000_000, 23_000_000]))
        self.assertEqual(gui.source_inventory(self.board), before)

    def test_missing_component_single_selection_and_copper_intersecting_region_refuse(self):
        for selected, region in (([self.selected[0]], self.region),
                                 ([self.selected[0], str(uuid.uuid4())], self.region),
                                 (self.selected, [7_000_000, 7_000_000, 31_000_000, 29_000_000])):
            with self.subTest(selected=selected, region=region), self.assertRaises(ValueError):
                intent.facts(self.inspection, intent.settings(selected, region))

    def test_unsupported_geometry_is_not_normalized_or_removed(self):
        pristine = self.board.read_bytes()
        for change in (lambda tree: sx.one(sx.children(tree, 'footprint')[0], 'at').append('45'),
                       lambda tree: tree.append(['group', '"unsupported"', ['uuid', json.dumps(str(uuid.uuid4()))]]),
                       lambda tree: sx.children(sx.children(tree, 'footprint')[0], 'pad')[0].__setitem__(2, 'smd')):
            self.board.write_bytes(pristine); self.rewrite(change); before = self.board.read_bytes()
            with self.subTest(change=change), self.assertRaises(ValueError): intent.inspect_saved(self.board)
            self.assertEqual(self.board.read_bytes(), before)

    def test_cardinal_pth_intake_is_visible_but_fixed_in_ordinary_scope(self):
        self.rewrite(lambda tree: sx.one(sx.children(tree, 'footprint')[0], 'at').append('90'))
        before = self.board.read_bytes()
        inspected = intent.inspect_saved(self.board)
        self.assertEqual(inspected['observation']['scope'], contract.ORDINARY_SCOPE)
        row = next(row for row in inspected['components'] if row['uuid'] == self.selected[0])
        self.assertTrue(row['fixed_reasons'])
        with self.assertRaises(ValueError):
            intent.facts(inspected, intent.settings(self.selected, self.region, scope=contract.ORDINARY_SCOPE))
        self.assertEqual(self.board.read_bytes(), before)

    def test_missing_project_or_linked_saved_input_refuses(self):
        project = self.board.with_suffix('.kicad_pro'); raw = project.read_bytes(); project.unlink()
        with self.assertRaises(ValueError): intent.inspect_saved(self.board)
        project.write_bytes(raw)
        link = self.root / 'linked.kicad_pcb'; link.symlink_to(self.board)
        with self.assertRaises(ValueError): intent.inspect_saved(link)

    def test_persisted_settings_are_exact_bounded_json_and_detached(self):
        path = self.root / 'placement settings.json'; path.write_text(json.dumps(self.options))
        loaded = intent.load_settings(path)
        self.assertEqual(loaded, self.options)
        loaded['selected'].clear(); self.assertEqual(len(self.options['selected']), 2)
        for raw in (b'{"schema":1,"schema":1}', b'{"value":NaN}', b'{"value":1e999}', b'{', b' ' * (64 * 1024 + 1)):
            path.write_bytes(raw)
            with self.subTest(raw=raw[:40]), self.assertRaises((ValueError, pipeline.Rejected)): intent.load_settings(path)
        path.write_text(json.dumps(self.options)); link = self.root / 'settings link'; link.symlink_to(path)
        with self.assertRaises((ValueError, pipeline.Rejected)): intent.load_settings(link)

    def test_settings_reject_authority_and_silent_policy_changes(self):
        changes = [('schema', True), ('preserve_existing', False), ('orientation', 'any'), ('side', 'back'),
                   ('selected', self.selected * 2), ('region_nm', [True, 7, 31, 13]),
                   ('search', dict(self.options['search'], seconds=2.0)), ('command', 'shell'), ('approval_granted', True)]
        for field, value in changes:
            changed = copy.deepcopy(self.options); changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): intent.validate_settings(changed)
        for key in self.options:
            changed = copy.deepcopy(self.options); del changed[key]
            with self.subTest(missing=key), self.assertRaises(ValueError): intent.validate_settings(changed)

    def test_real_pure_search_preserves_source_and_only_proposes_valid_selected_moves(self):
        before = copy.deepcopy(self.inspection)
        with patch('subprocess.Popen', side_effect=AssertionError('search must not execute commands')):
            proposal = self.proposal()
        self.assertEqual(self.inspection, before)
        self.assertEqual(gui.source_inventory(self.board), self.original)
        facts = intent.facts(self.inspection, self.options)
        self.assertEqual(proposal['search']['upstream_commit'], intent.prototype.UPSTREAM_COMMIT)
        self.assertLessEqual(len(proposal['search']['alternatives']), 2)
        for row in proposal['search']['alternatives']:
            constraints.validate_alternative(facts, row['candidate'])
            self.assertEqual(set(row['moves_nm']), set(self.selected))
            self.assertTrue(all(type(number) is int for xy in row['moves_nm'].values() for number in xy))
        for field in ('native_validation_performed', 'execution_authorized', 'approval_granted'):
            self.assertIs(proposal[field], False)

    def test_already_cancelled_search_returns_no_alternative(self):
        event = threading.Event(); event.set()
        result = intent.propose(self.inspection, self.options, cancel_event=event)
        self.assertEqual(result['search']['status'], 'cancelled')
        self.assertEqual(result['search']['alternatives'], [])
        self.assertEqual(gui.source_inventory(self.board), self.original)
        with self.assertRaises(ValueError): intent.Review(result)
        with self.assertRaises(ValueError): intent.propose(self.inspection, self.options, cancel_event=object())

    def test_late_cancellation_or_source_change_cannot_return_positive_proposal(self):
        proposer = intent.prototype.propose; event = threading.Event()
        def cancel(*args, **kwargs):
            result = proposer(*args, **kwargs); event.set(); return result
        with patch.object(intent.prototype, 'propose', side_effect=cancel):
            result = intent.propose(self.inspection, self.options, cancel_event=event)
        self.assertEqual(result['search']['status'], 'cancelled'); self.assertEqual(result['search']['alternatives'], [])
        def mutate(*args, **kwargs):
            result = proposer(*args, **kwargs)
            self.board.with_suffix('.kicad_pro').write_bytes(self.board.with_suffix('.kicad_pro').read_bytes() + b'\n')
            return result
        with patch.object(intent.prototype, 'propose', side_effect=mutate), self.assertRaisesRegex(ValueError, 'source changed'):
            intent.propose(self.inspection, self.options)

    def test_forged_inspection_and_changed_sidecar_refuse(self):
        for field, value in [('native_validation_performed', True), ('approval_granted', True), ('components', [])]:
            changed = copy.deepcopy(self.inspection); changed[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'source changed'): intent.current(changed)
        self.board.with_suffix('.kicad_prl').write_bytes(self.board.with_suffix('.kicad_prl').read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'source changed'): intent.propose(self.inspection, self.options)

    def original_review(self, inspection=None, settings=None):
        inspection = self.inspection if inspection is None else inspection
        settings = self.options if settings is None else settings
        facts = intent.facts(inspection, settings)
        return intent.Review(dict(kind='autorouter.placement-proposals.v1',
            inspection=copy.deepcopy(inspection), settings=copy.deepcopy(settings),
            search=dict(status='proposals_ready', alternatives=[dict(candidate=constraints.original_alternative(facts))])))

    def test_combined_swap_succeeds_when_both_individual_edits_collide(self):
        ordinary_board = ordinary_fixture.write_project(self.root / 'ordinary project')
        ordinary_inspection = intent.inspect_saved(ordinary_board)
        ordinary_settings = intent.settings(ordinary_fixture.selected(), self.region, scope=contract.ORDINARY_SCOPE)
        for inspection, settings in ((self.inspection, self.options), (ordinary_inspection, ordinary_settings)):
            with self.subTest(scope=intent.settings_scope(settings)):
                review = self.original_review(inspection, settings)
                a, b = settings['selected']
                before = copy.deepcopy(review.moves); pose = copy.deepcopy(review.pose); revision = review.revision
                edits = {a: ['26', '10'], b: ['12', '10']}
                for identity, xy in edits.items():
                    review.decision(acknowledged=True, accepted=True)
                    with self.assertRaises(ValueError):review.edit(identity, *xy)
                    self.assertEqual(review.moves, before); self.assertEqual(review.pose, pose)
                    self.assertEqual(review.revision, revision); self.assertIsNone(review.intent)
                review.decision(acknowledged=True, accepted=True)
                with patch.object(contract, 'validate_moves', wraps=contract.validate_moves) as validate, \
                        patch.object(review, '_adopt', wraps=review._adopt) as adopt:
                    review.edit_many(edits)
                self.assertEqual(validate.call_count, 1); self.assertEqual(adopt.call_count, 1)
                self.assertEqual(review.moves, {a: [26_000_000, 10_000_000], b: [12_000_000, 10_000_000]})
                self.assertEqual(review.revision, revision + 1); self.assertIsNone(review.intent)
                draft = review.decision(acknowledged=True, accepted=True)
                self.assertEqual(intent.validate_draft(inspection, draft), draft)
                for key in ('approval_granted', 'execution_authorized', 'native_validation_performed',
                            'routing_accepted', 'warning_acknowledged', 'human_PCB_approval'):
                    self.assertIs(draft[key], False)
                edits[a][0] = '99'
                self.assertEqual(review.moves[a][0], 26_000_000)
                self.assertEqual(gui.source_inventory(Path(inspection['source'])), inspection['source_hashes'])

    def test_edit_many_errors_revoke_intent_without_partial_pose_or_revision_change(self):
        review = self.original_review(); a, b = self.selected
        cases = [None, [], (), {}, {True: ['14', '10']},
                 {str(uuid.uuid4()): ['14', '10']},
                 {multipad_fixture.uid('J3-footprint'): ['14', '10']},
                 {a: ['14', '10'], b: ['24', '10'], 'extra': ['1', '2']},
                 {a: None}, {a: ('14', '10')}, {a: '14,10'}, {a: ['14']}, {a: ['14', '10', '0']},
                 {a: [14, '10']}, {a: [True, '10']}, {a: ['', '10']}, {a: ['1' * 33, '10']},
                 {a: ['not decimal', '10']}, {a: ['NaN', '10']}, {a: ['sNaN', '10']},
                 {a: ['Infinity', '10']}, {a: ['1e999999', '10']}, {a: ['2001', '10']},
                 {a: ['1', '1']}, {a: ['14', '10'], b: ['15', '10']},
                 {a: ['14', '10'], b: ['24', 'NaN']}]
        for edits in cases:
            review.decision(acknowledged=True, accepted=True)
            before = (copy.deepcopy(review.pose), copy.deepcopy(review.moves), review.revision)
            with self.subTest(edits=edits), patch.object(review, '_adopt', wraps=review._adopt) as adopt:
                with self.assertRaises(ValueError):review.edit_many(edits)
                adopt.assert_not_called()
            self.assertIsNone(review.intent)
            self.assertEqual((review.pose, review.moves, review.revision), before)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_edit_many_subset_keeps_unedited_pose_and_decimal_rules(self):
        review = self.original_review(); a, b = self.selected
        before = copy.deepcopy(review.moves); revision = review.revision
        review.edit_many({a: [' 1.40000015e1 ', '+10']})
        self.assertEqual(review.moves[a], [14_000_002, 10_000_000])
        self.assertEqual(review.moves[b], before[b])
        self.assertEqual(review.revision, revision + 1)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_single_edit_delegates_and_preserves_refusal_messages(self):
        review = self.original_review(); a = self.selected[0]
        with patch.object(review, 'edit_many', wraps=review.edit_many) as many:
            review.edit(a, '14', '10')
        many.assert_called_once_with({a: ['14', '10']})
        for component, x, y, message in (([], '14', '10', 'Only selected movable components'),
                                         (a, 14, '10', 'Enter bounded decimal coordinates'),
                                         (a, 'NaN', '10', 'Coordinates must be finite'),
                                         (a, 'nope', '10', 'Enter decimal coordinates')):
            review.decision(acknowledged=True, accepted=True)
            before = (copy.deepcopy(review.pose), copy.deepcopy(review.moves), review.revision)
            with self.subTest(component=component, x=x), self.assertRaisesRegex(ValueError, message):
                review.edit(component, x, y)
            self.assertIsNone(review.intent)
            self.assertEqual((review.pose, review.moves, review.revision), before)

    def test_edit_many_revision_limit_retains_prior_pose_after_refusal(self):
        review = self.original_review(); review.revision = 256
        review.decision(acknowledged=True, accepted=True)
        before = (copy.deepcopy(review.pose), copy.deepcopy(review.moves), review.revision)
        with self.assertRaisesRegex(ValueError, 'Review edit limit reached'):
            review.edit_many({self.selected[0]: ['14', '10']})
        self.assertIsNone(review.intent)
        self.assertEqual((review.pose, review.moves, review.revision), before)

    def test_exact_edited_draft_validates_but_never_grants_execution(self):
        review = self.review()
        review.edit(self.selected[0], '26.2', format(review.moves[self.selected[0]][1] / 1e6, '.6f'))
        draft = review.decision(acknowledged=True, accepted=True)
        checked = intent.validate_draft(self.inspection, draft)
        self.assertEqual(checked, draft)
        self.assertEqual(checked['moves_nm'][self.selected[0]][0], 26_200_000)
        for field in ('native_validation_performed', 'execution_authorized', 'approval_granted', 'routing_accepted',
                      'warning_acknowledged', 'human_PCB_approval'):
            self.assertIs(checked[field], False)
        checked['moves_nm'].clear(); self.assertTrue(review.moves)
        self.assertEqual(gui.source_inventory(self.board), self.original)

    def test_review_changes_revoke_intent_and_rejection_never_qualifies(self):
        review = self.review(); review.decision(acknowledged=True, accepted=True)
        review.choose(0); self.assertIsNone(review.intent)
        review.decision(acknowledged=True, accepted=True)
        current = review.moves[self.selected[0]]
        review.edit(self.selected[0], format(current[0] / 1e6, '.6f'), format(current[1] / 1e6, '.6f'))
        self.assertIsNone(review.intent)
        rejected = review.decision(acknowledged=True, accepted=False)
        self.assertEqual(rejected['choice'], 'reject')
        with self.assertRaises(ValueError): intent.validate_draft(self.inspection, rejected)
        for acknowledged, accepted in ((False, True), (1, True), (True, 1)):
            with self.assertRaises(ValueError): review.decision(acknowledged=acknowledged, accepted=accepted)
            self.assertIsNone(review.intent)

    def test_fixed_or_invalid_edit_refuses_without_changing_pose(self):
        review = self.review(); old = copy.deepcopy(review.moves)
        for part, x, y in ((multipad_fixture.uid('J3-footprint'), '20', '10'),
                           (self.selected[0], '3000', '10'), (self.selected[0], 'nan', '10'),
                           (self.selected[0], '1', '1'), (self.selected[0], '1e999999', '10')):
            with self.subTest(part=part, x=x), self.assertRaises(ValueError): review.edit(part, x, y)
            self.assertEqual(review.moves, old)

    def test_stale_extra_authority_or_changed_draft_fields_refuse(self):
        review = self.review(); draft = review.decision(acknowledged=True, accepted=True)
        changes = [('choice', 'reject'), ('execution_authorized', True), ('approval_granted', True),
                   ('routing_accepted', True), ('warning_acknowledged', True), ('human_PCB_approval', True),
                   ('schema', True), ('revision', True), ('revision', 257), ('source', 'other'),
                   ('pose_sha256', '0' * 64), ('inspection_sha256', '0' * 64), ('command', 'shell')]
        for field, value in changes:
            changed = copy.deepcopy(draft); changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): intent.validate_draft(self.inspection, changed)
        for key in draft:
            changed = copy.deepcopy(draft); del changed[key]
            with self.subTest(missing=key), self.assertRaises(ValueError): intent.validate_draft(self.inspection, changed)
        self.board.with_suffix('.kicad_sch').write_bytes(self.board.with_suffix('.kicad_sch').read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'source changed'): review.decision(acknowledged=True, accepted=True)
        self.assertIsNone(review.intent)
        with self.assertRaisesRegex(ValueError, 'source changed'): intent.validate_draft(self.inspection, draft)


if __name__ == '__main__': unittest.main()
