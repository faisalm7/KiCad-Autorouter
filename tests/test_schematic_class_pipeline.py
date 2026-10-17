"""Pure central class-proof plumbing; no Native, GUI or routing execution.

SPDX-License-Identifier: GPL-3.0-or-later

Route tests mock the evidence reader to observe exact central call arguments.
Export controls reuse the existing constructed-worker seam. These tests
establish neither Native class correctness nor GUI qualification.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import uuid

from autorouter import __main__ as cli, gui, pipeline as p, preferences as pref
from autorouter import placement_clearance as pc, review_export, schematic_class_evidence as classes, sexpr as sx
from experiments.schematic_class_intent_v1 import fixture
from tests import test_review_export as prior_export


def encoded(tree):
    return (sx.dump(tree)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class SchematicClassPipelineControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.project = self.root/'source'; self.project.mkdir()
        payload = fixture.files()
        sch = sx.parse(payload[fixture.STEM+'.kicad_sch'].decode())
        sx.one(sx.one(sch, 'netclass_flag'), 'property')[2] = '"POWER"'
        payload[fixture.STEM+'.kicad_sch'] = encoded(sch)
        for name, raw in payload.items(): (self.project/name).write_bytes(raw)
        self.board = self.project/(fixture.STEM+'.kicad_pcb')
        self.original = sx.read(self.board)
        # An unlocked source route alongside the fixture's10locked KEEP routes
        # makes whole-board vs partial task reconstruction distinguishable.
        route = copy.deepcopy(p.routes(self.original)[0])
        route[:] = [node for node in route if node != ['locked', 'yes']]
        sx.one(route, 'net')[1] = '"ROUTE"'
        sx.one(route, 'uuid')[1] = json.dumps(str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-class-plumbing-unlocked')))
        self.original.append(route); self.board.write_bytes(encoded(self.original))
        self.output = self.root/'job'; self.output.mkdir(); (self.output/'candidate').mkdir()
        for path in self.project.iterdir(): shutil.copy2(path, self.output/'candidate'/path.name)
        self.candidate = self.output/'candidate'/self.board.name
        final = copy.deepcopy(self.original)
        addition = copy.deepcopy(route)
        sx.one(addition, 'uuid')[1] = json.dumps(str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-class-plumbing-final')))
        final.append(addition); self.candidate.write_bytes(encoded(final))

    def record(self, scope='whole_board_unlocked_routing'):
        task = p.routing_task(self.original, scope)
        return {'schema': 1, 'engine_profile': 'standard', 'scope': scope,
            'source': str(self.board), 'source_hashes': pc.inventory(self.project),
            'candidate_sha256': sha(pc.read_bytes(self.candidate)),
            'task_sha256': sha(encoded(task)),
            'schematic_class_task': {'constructed': 'task'},
            'schematic_class_final': {'constructed': 'final'}}

    def unflag(self):
        path = self.board.with_suffix('.kicad_sch'); sch = sx.read(path)
        sch.remove(sx.one(sch, 'netclass_flag')); path.write_bytes(encoded(sch))

    def context(self, data, **kwargs):
        return p.class_context_for_record(data, self.output, input_policy='native', **kwargs)

    def check(self, data, context=classes.CONTEXT):
        return p.check_route_class_evidence(self.output, data, self.original, self.candidate,
                                           class_context=context)

    def test_route_preview_reports_pending_and_never_native_or_routing_acceptance(self):
        before = pc.inventory(self.project)
        with patch('subprocess.run', side_effect=AssertionError('preview must not execute a worker')):
            result = cli.preview(self.board, purpose='route')
        pending = result['schematic_class_check']
        self.assertEqual(result['status'], 'preview')
        self.assertIs(result['static_preflight_passed'], True)
        self.assertIs(result['native_validation_performed'], False)
        self.assertEqual(pending['context'], classes.CONTEXT)
        self.assertEqual(pending['status'], 'pending_native_class_parity')
        for key in ('class_parity_qualified', 'accepted', 'routing_accepted', 'production_qualified'):
            self.assertIs(pending[key], False)
        self.assertEqual(pc.inventory(self.project), before)
        text = gui.human_summary('preview', result)
        self.assertIn('verify schematic/PCB class bindings before routing starts', text)
        self.assertIn('Native routing validation has not run', text)
        self.assertNotIn('Original-design checks passed', text)

    def test_improve_and_default_preflight_still_refuse_flags(self):
        with self.assertRaisesRegex(p.Rejected, 'netclass_flag unsupported'):
            p.preflight(self.board)
        with self.assertRaisesRegex(p.Rejected, 'netclass_flag unsupported'):
            cli.preview(self.board, purpose='improve')
        for context in ('legacy', '', True):
            with self.subTest(context=context), self.assertRaisesRegex(p.Rejected, 'unknown schematic class context'):
                p.preflight(self.board, class_context=context)

    def test_even_explicit_route_preview_refuses_hierarchy(self):
        path = self.board.with_suffix('.kicad_sch'); sch = sx.read(path)
        sch.append(['sheet', ['property', '"Sheetfile"', '"child.kicad_sch"']]); path.write_bytes(encoded(sch))
        with self.assertRaisesRegex(p.Rejected, 'hierarchy'):
            cli.preview(self.board, purpose='route')

    def test_context_accepts_only_ordinary_schema1_native_whole_partial_records(self):
        for scope in ('whole_board_unlocked_routing', 'partial_completion'):
            for profile in ('standard', 'tuned', 'completion-only'):
                with self.subTest(scope=scope, profile=profile):
                    data = self.record(scope); data['engine_profile'] = profile
                    self.assertEqual(self.context(data), classes.CONTEXT)
        for key, value in (('schema', True), ('schema', 3), ('scope', 'selected_nets'),
                           ('scope', 'unknown'), ('engine_profile', 'tuned-free-angle'),
                           ('strategy', None), ('engine_fanout_override', False),
                           ('engine_optimizer_override', False), ('engine_angle_binding', {})):
            with self.subTest(key=key, value=value):
                data = self.record(); data[key] = value
                self.assertIsNone(self.context(data))
        self.assertIsNone(self.context(self.record(), native_toolchain=object()))
        self.assertIsNone(p.class_context_for_record(self.record(), self.output,
                                                   input_policy='placement-search-v1'))

    def test_context_preserves_support_for_real_protected_whole_and_partial_records(self):
        for scope in ('whole_board_unlocked_routing', 'partial_completion'):
            with self.subTest(scope=scope):
                data = self.record(scope)
                data['protected_routes'] = len(p.protected_for_record(data, self.original))
                data['protected_route_import'] = {'policy': 'exact_non_uuid_lock_position_v2',
                    'matches': [{'constructed': 'protected match'}],
                    'transplanted_routes_sha256': '1'*64, 'imported_sha256': '2'*64}
                self.assertGreater(data['protected_routes'], 0)
                self.assertEqual(self.context(data), classes.CONTEXT)

    def test_context_returns_none_for_malformed_or_unsupported_captured_choices(self):
        for change in ({'guidance_policy': 'board-floors-v1'},
                       {'routing_preferences': {}}, {'routing_preferences': {'effective': None}}):
            with self.subTest(change=change):
                self.assertIsNone(self.context({**self.record(), **change}))
        settings = dict(pref.DEFAULTS); settings.update(profile='completion-only', layers=['F.Cu'])
        data = self.record(); data['routing_preferences'] = {'effective': settings}
        self.assertIsNone(self.context(data))

    def test_context_refuses_experimental_or_diagnostic_markers(self):
        for key in ('experimental_route_policy', 'experimental_native_toolchain',
                    'experimental_schematic_parity_policy', 'diagnostic_schema',
                    'production_admitted', 'production_qualified'):
            with self.subTest(key=key):
                self.assertIsNone(self.context({**self.record(), key: False}))

    def test_replay_reconstructs_exact_task_and_keeps_protected_routes(self):
        final_raw = pc.read_bytes(self.candidate)
        for scope in ('whole_board_unlocked_routing', 'partial_completion'):
            with self.subTest(scope=scope), patch.object(classes, 'check', autospec=True) as checker, \
                    patch.object(classes, 'check_local_settings', autospec=True) as local_guard:
                data = self.record(scope)
                self.assertIs(self.check(data), True)
                self.assertEqual([call.args[2] for call in checker.call_args_list], ['task', 'final'])
                task_raw = checker.call_args_list[0].kwargs['board_raw']
                self.assertEqual(task_raw, encoded(p.routing_task(self.original, scope)))
                self.assertNotEqual(task_raw, final_raw)
                task = sx.parse(task_raw.decode())
                protected = p.protected_for_record(data, self.original)
                self.assertEqual(p.routes(task), protected)
                self.assertTrue(all(route in p.routes(task) for route in protected))
                self.assertEqual(checker.call_args_list[1].kwargs['board_raw'], final_raw)
                self.assertEqual(checker.call_args_list[0].kwargs['native_map'], self.output/'export-netclasses.json')
                self.assertEqual(checker.call_args_list[1].kwargs['native_map'], self.output/'final-netclasses.json')
                for call in checker.call_args_list:
                    self.assertEqual(call.kwargs['source'], str(self.candidate))
                    self.assertEqual(call.kwargs['project_raw'], pc.read_bytes(self.candidate.with_suffix('.kicad_pro')))
                    self.assertEqual(call.kwargs['schematic_raw'], pc.read_bytes(self.candidate.with_suffix('.kicad_sch')))
                self.assertEqual([call.args[1] for call in local_guard.call_args_list], ['task', 'final'])

    def test_required_both_stages_survive_receipt_key_deletion(self):
        for removed in (('schematic_class_task',), ('schematic_class_final',),
                        ('schematic_class_task', 'schematic_class_final')):
            with self.subTest(removed=removed), patch.object(classes, 'check', autospec=True) as checker:
                data = self.record()
                for key in removed: del data[key]
                with self.assertRaisesRegex(p.Rejected, 'missing source and final'):
                    self.check(data)
                checker.assert_not_called()

    def test_wrong_task_hash_and_failed_final_stage_cannot_pass(self):
        with patch.object(classes, 'check', autospec=True) as checker:
            data = self.record(); data['task_sha256'] = sha(pc.read_bytes(self.candidate))
            with self.assertRaisesRegex(p.Rejected, 'routing task differs'): self.check(data)
            checker.assert_not_called()
        with patch.object(classes, 'check', side_effect=[{'constructed': True}, ValueError('stale final proof')]):
            with self.assertRaisesRegex(ValueError, 'stale final proof'): self.check(self.record())

    def test_route_late_reader_mutation_of_candidate_source_or_evidence_refuses(self):
        candidate_before = pc.read_bytes(self.candidate)
        schematic = self.board.with_suffix('.kicad_sch'); schematic_before = pc.read_bytes(schematic)
        late = self.output/'late-class-evidence.json'
        for kind in ('candidate', 'source', 'evidence'):
            with self.subTest(kind=kind):
                data = self.record()
                def mutate(directory, record, stage, **kwargs):
                    if stage == 'final':
                        if kind == 'candidate': self.candidate.write_bytes(candidate_before+b'\n')
                        elif kind == 'source': schematic.write_bytes(schematic_before+b'\n')
                        else: late.write_text('{}\n')
                    return {'constructed': 'class proof'}
                try:
                    with patch.object(classes, 'check', side_effect=mutate), \
                            patch.object(classes, 'check_local_settings', autospec=True) as local_guard:
                        with self.assertRaises((ValueError, p.Rejected)): self.check(data)
                        local_guard.assert_not_called()
                finally:
                    self.candidate.write_bytes(candidate_before); schematic.write_bytes(schematic_before)
                    if late.exists(): late.unlink()

    def test_export_late_reader_mutation_of_candidate_source_or_evidence_refuses(self):
        candidate_before = pc.read_bytes(self.candidate)
        schematic = self.board.with_suffix('.kicad_sch'); schematic_before = pc.read_bytes(schematic)
        late = self.output/'late-class-evidence.json'
        for kind in ('candidate', 'source', 'evidence'):
            with self.subTest(kind=kind):
                report = self.record(); data = copy.deepcopy(report); del data['schematic_class_task']
                binding = {'source': str(self.board), 'source_hashes': report['source_hashes'],
                           'receipt': str(self.output/'result.json'), 'input_policy': 'native'}
                def mutate(*args, **kwargs):
                    if kind == 'candidate': self.candidate.write_bytes(candidate_before+b'\n')
                    elif kind == 'source': schematic.write_bytes(schematic_before+b'\n')
                    else: late.write_text('{}\n')
                    return {'constructed': 'class proof'}
                try:
                    with patch.object(classes, 'check', side_effect=mutate), \
                            patch.object(classes, 'check_local_settings', autospec=True) as local_guard:
                        with self.assertRaises((ValueError, p.Rejected)):
                            review_export.check_class_evidence(self.output, data, binding, report)
                        local_guard.assert_not_called()
                finally:
                    self.candidate.write_bytes(candidate_before); schematic.write_bytes(schematic_before)
                    if late.exists(): late.unlink()

    def test_default_context_still_refuses_instead_of_adopting_class_proofs(self):
        with patch.object(classes, 'check', autospec=True) as checker:
            with self.assertRaisesRegex(p.Rejected, 'netclass_flag unsupported'):
                self.check(self.record(), context=None)
            checker.assert_not_called()

    def test_unflagged_source_refuses_unexpected_metadata_and_binding(self):
        self.unflag()
        with patch.object(classes, 'check', autospec=True) as checker:
            with self.assertRaisesRegex(p.Rejected, 'unexpected schematic class evidence'):
                self.check(self.record())
            data = self.record(); del data['schematic_class_task']; del data['schematic_class_final']
            (self.output/'task-classes-binding.json').write_text('{}\n')
            with self.assertRaisesRegex(p.Rejected, 'unexpected schematic class evidence'): self.check(data)
            checker.assert_not_called()

    def test_unflagged_orphan_class_proof_namespace_is_not_silently_ignored(self):
        self.unflag()
        for name in ('task-classes-proof.json', 'final-classes.net',
                     'task-classes-netlist-process.json', 'final-classes-netlist.log',
                     'task-classes-input'):
            with self.subTest(name=name), patch.object(classes, 'check', autospec=True) as checker:
                data = self.record(); del data['schematic_class_task']; del data['schematic_class_final']
                path = self.output/name
                if name.endswith('-input'): path.mkdir()
                else: path.write_text('constructed\n')
                try:
                    with self.assertRaisesRegex(p.Rejected, 'unexpected schematic class evidence'): self.check(data)
                    checker.assert_not_called()
                finally:
                    if path.is_dir(): path.rmdir()
                    else: path.unlink()

    def test_gui_improve_preview_argv_carries_refusal_purpose(self):
        output_parent = self.root/'gui-outputs'; output_parent.mkdir()
        for method in ('route', 'improve'):
            with self.subTest(method=method):
                settings = dict(pref.DEFAULTS)
                if method == 'improve': settings['profile'] = 'tuned'
                workflow = gui.Request(str(self.board), str(output_parent), json.dumps(settings), True, method).prepare()
                argv = workflow.command('preview')
                if method == 'improve': self.assertEqual(argv[-2:], ['--purpose', 'improve'])
                else: self.assertNotIn('--purpose', argv)
                self.assertNotIn('route', argv[4:5])

    def test_export_allows_only_final_class_step_and_keeps_existing_process_limits(self):
        folder = self.root/'export-step'; folder.mkdir()
        job = SimpleNamespace(out=folder, steps=[], env={}, remaining=lambda: 120., native_toolchain=None)
        argv = [str(p.c.CLI), 'sch', 'export', 'netlist', '--format', 'kicadsexpr',
                '--output', str(folder/'final-classes.net'), str(self.candidate.with_suffix('.kicad_sch'))]
        synthetic = {'status': 'success', 'exit_code': 0, 'cleanup_complete': True,
                     'log': str(folder/'final-classes-netlist.log'), 'log_bytes': 0, 'log_truncated': False}
        with patch.object(review_export, 'run', return_value=synthetic) as worker:
            result = review_export.ExportJob.step(job, 'final-classes-netlist', argv)
            self.assertEqual(result['name'], 'final-classes-netlist')
            self.assertEqual(worker.call_args.args[0], [*review_export.f.SANDBOX, *argv])
            self.assertEqual(worker.call_args.kwargs['timeout'], 30)
            self.assertEqual(worker.call_args.kwargs['max_workdir_bytes'], review_export.OUTPUT_BYTES)
            self.assertEqual(worker.call_args.kwargs['max_group_rss_bytes'], 2*1024**3)
            self.assertEqual(worker.call_args.kwargs['max_log_bytes'], 512*1024)
            for name in ('task-classes-netlist', 'engine', 'export', 'import', 'unknown'):
                with self.subTest(name=name), self.assertRaisesRegex(p.Rejected, 'prohibits'):
                    review_export.ExportJob.step(job, name, argv)
            self.assertEqual(worker.call_count, 1)

    def test_late_export_namespace_insertion_after_final_byte_witness_refuses(self):
        # Reuse the existing genuine transaction/reader with constructed Native
        # workers. Inject a class artifact AFTER the final evidence witness was
        # captured: the new late class hook must still detect the unsupported
        # namespace. No second fake Native invocation or new verifier is needed.
        case = prior_export.ExportControls(); self.addCleanup(case.doCleanups); case.setUp()
        case.export(); self.assertTrue(review_export.check_export(case.output/'export.json')['current'])
        original = review_export.evidence; calls = []
        def mutate_after_witness(folder):
            result = original(folder)
            if Path(folder) == case.output:
                calls.append(str(folder))
                if len(calls) == 2:
                    (case.output/'validation/final-classes-proof.json').write_text('{}\n')
            return result
        with patch.object(review_export, 'evidence', side_effect=mutate_after_witness):
            with self.assertRaisesRegex(p.Rejected, 'unexpected export class proof'):
                review_export.check_export(case.output/'export.json')
        self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
