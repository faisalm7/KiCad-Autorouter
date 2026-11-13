"""Qualification admission, lifecycle and late-fence controls; no Native runs.

The retained-check harness substitutes its Native proof only to isolate process
receipt admission. It must never be cited as actual placement qualification.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import placement as placement
from autorouter import floor_route, pipeline


class QualificationAdmission(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='placement-qualification-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.runtime = self.root / 'runtime'; (self.runtime / '.runs').mkdir(parents=True)
        self.source = self.root / 'source'; self.source.mkdir()
        self.board = self.source / 'owned.kicad_pcb'; self.board.write_text('owned fixture\n')

    def test_literal_execution_confirmation_required_before_binding_or_output(self):
        for confirmed in (False, 1, 'yes', None):
            with self.subTest(confirmed=confirmed), patch.object(placement, '_binding') as binding, self.assertRaises(ValueError):
                placement.qualify('unused', '0' * 64, 'unused', confirmed=confirmed)
            binding.assert_not_called()

    def test_hidden_worker_refuses_outside_runtime_before_reading_or_creating(self):
        outside = self.root / 'unrelated'; outside.mkdir()
        with patch.object(placement.c, 'ROOT', self.runtime), \
                patch.object(placement.f, 'read_json', side_effect=AssertionError('read before worker scope check')) as read, \
                patch.object(placement.f, 'FloorJob') as job, self.assertRaises(ValueError):
            placement._worker(outside, '0' * 64)
        read.assert_not_called(); job.assert_not_called(); self.assertEqual(list(outside.iterdir()), [])

    def test_low_space_refuses_before_output_creation_or_worker(self):
        output = self.runtime / '.runs' / 'fresh-job'
        binding = dict(inspection={'source': str(self.board)})
        with patch.object(placement.c, 'ROOT', self.runtime), patch.object(placement, '_binding', return_value=binding), \
                patch('shutil.disk_usage', return_value=SimpleNamespace(free=placement.DISK_BYTES + 3 * 1024**3 - 1)), \
                patch('autorouter.runner.run') as run, self.assertRaisesRegex(ValueError, 'insufficient'):
            placement.qualify('unused', '0' * 64, output, confirmed=True)
        self.assertFalse(output.exists()); run.assert_not_called()

    def test_nonfresh_or_source_nested_output_refuses_before_worker(self):
        binding = dict(inspection={'source': str(self.board)})
        existing = self.runtime / '.runs' / 'existing'; existing.mkdir()
        for output in (existing, self.source / 'nested', self.root / 'another'):
            with self.subTest(output=output), patch.object(placement.c, 'ROOT', self.runtime), \
                    patch.object(placement, '_binding', return_value=binding), patch('autorouter.runner.run') as run, \
                    self.assertRaises(ValueError):
                placement.qualify('unused', '0' * 64, output, confirmed=True)
            run.assert_not_called()

    def test_boolean_or_float_worker_schema_refuses_before_accounting_or_payload(self):
        output = self.runtime / '.runs' / 'schema'; output.mkdir()
        (output / 'binding.json').write_text('{}')
        binding = dict(inspection={'source': str(self.board)}, tools={})
        for schema in (True, 1.0, None):
            data = dict(schema=schema, kind=placement.KIND, status='pending_candidate', placement_qualified=True,
                external_exit_required=True, tools={}, binding_sha256=placement.p.sha(output / 'binding.json'),
                budget_seconds=placement.WORKER_SECONDS, cpu_budget_seconds=placement.WORKER_SECONDS,
                **{key: False for key in placement.AUTHORITY})
            with self.subTest(schema=schema), patch.object(placement.p, 'check_resource_accounting',
                    side_effect=AssertionError('malformed schema reached accounting')) as accounting, self.assertRaises(ValueError):
                placement.proof(output, binding, data)
            accounting.assert_not_called()


class MaterialFences(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='placement-material-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.manifest = self.root / 'runtime-distribution.json'; self.manifest.write_text('manifest')
        self.wrapper = self.root / 'pcbnew.py'; self.wrapper.write_text('wrapper')
        self.native = self.root / '_pcbnew.so'; self.native.write_bytes(b'native fixture')
        self.draft = self.root / 'draft.json'; self.draft.write_text('reviewed draft')
        self.code = self.root / 'worker-code.py'; self.code.write_text('code fixture')
        self.tool = self.root / 'tool'; self.tool.write_bytes(b'original tool')
        self.tools = {'files': {'tool': self.sha(self.tool)}}
        self.binding = dict(runtime=str(self.root), runtime_manifest_sha256=self.sha(self.manifest),
            code_sha256={'worker': self.sha(self.code)}, draft=str(self.draft), draft_sha256=self.sha(self.draft),
            inspection={'source': str(self.root / 'source.kicad_pcb')}, tools=copy.deepcopy(self.tools),
            wrapper_sha256=self.sha(self.wrapper))

    def sha(self, path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def material(self, *, tool_read=None, source_read=None):
        if tool_read is None: tool_read = lambda: {'files': {'tool': self.sha(self.tool)}}
        with patch.object(placement.c, 'ROOT', self.root), patch.object(placement.c, 'NATIVE_VERSION', '10.0.7'), \
                patch.object(placement.c, 'PCBNEW', self.native), \
                patch.object(placement, 'code_pins', side_effect=lambda: {'worker': self.sha(self.code)}), \
                patch.object(placement.intent, 'current', side_effect=source_read), \
                patch.object(placement.p, 'tool_manifest', side_effect=tool_read):
            return placement.material(self.binding)

    def test_actual_changed_tool_material_refuses_even_if_manifest_file_is_unchanged(self):
        self.tool.write_bytes(b'changed tool')
        with self.assertRaises(ValueError): self.material()

    def test_late_tool_read_cannot_change_already_checked_draft_dependency_or_manifest(self):
        for path in (self.draft, self.code, self.manifest, self.wrapper):
            raw = path.read_bytes()
            def mutate(path=path):
                path.write_bytes(b'changed late')
                return copy.deepcopy(self.tools)
            with self.subTest(path=path.name), self.assertRaises(ValueError): self.material(tool_read=mutate)
            path.write_bytes(raw)

    def test_source_change_during_tool_read_is_checked_before_return(self):
        changed = []
        def mutate():
            changed.append(True)
            return copy.deepcopy(self.tools)
        def source(_):
            if changed: raise ValueError('source changed during tool read')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.material(tool_read=mutate, source_read=source)


class RetainedControllerAdmission(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='placement-check-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / '.runs' / 'closed'; (self.output / 'work').mkdir(parents=True)
        (self.output / 'work' / 'result.json').write_text('{}')
        self.binding = dict(draft=str(self.root / 'draft.json'), draft_sha256='0' * 64)
        self.write('binding.json', self.binding)
        self.digest = placement.p.sha(self.output / 'binding.json')
        with patch.object(placement.c, 'ROOT', self.root):
            argv = placement._worker_argv(self.output, self.digest)
        self.process = dict(status='success', exit_code=0, cleanup_complete=True, log_truncated=False,
            argv=argv, cwd=str(self.output), wall_seconds=10., cpu_seconds=8., monitor_cpu_seconds=0.,
            resource_guards=dict(max_group_rss_bytes=placement.RSS_BYTES, max_workdir_bytes=placement.DISK_BYTES,
                                 os_enforced=False))
        self.result = {'candidate': str(self.output / 'work' / 'candidate.kicad_pcb')}
        self.outer = dict(schema=1, kind=placement.KIND, status='pending_candidate', placement_qualified=True,
            **{key: False for key in placement.AUTHORITY}, total_seconds=placement.TOTAL_SECONDS,
            worker_seconds=placement.WORKER_SECONDS, controller_exit_not_measured=True, publication_allowance_seconds=1,
            wall_seconds=20., full_cpu_seconds=20., binding_sha256=self.digest,
            worker_artifact_hashes=placement.pc.inventory(self.output / 'work'), result=self.result)

    def write(self, name, value):
        (self.output / name).write_text(json.dumps(value))

    def check(self, process=None, outer=None, *, mutation=None):
        self.write('process.json', self.process if process is None else process)
        actual = copy.deepcopy(self.outer if outer is None else outer)
        actual['process_sha256'] = placement.p.sha(self.output / 'process.json'); self.write('result.json', actual)
        def proof(*_, **kwargs):
            self.assertIs(kwargs.get('replay'), True)
            if mutation is not None: mutation()
            return copy.deepcopy(self.result)
        with patch.object(placement.c, 'ROOT', self.root), patch.object(placement, '_binding', return_value=self.binding), \
                patch.object(placement, 'material'), patch.object(placement, 'proof', side_effect=proof):
            return placement.check(self.output)

    def test_controller_admission_harness_is_pending_without_native_authority(self):
        result = self.check()
        self.assertTrue(result['placement_qualified'])
        for name in placement.AUTHORITY: self.assertIs(result[name], False)

    def test_cancel_failed_cleanup_truncation_and_wrong_command_refuse(self):
        for key, value in [('status', 'cancelled'), ('exit_code', -9), ('exit_code', False),
                           ('cleanup_complete', False), ('log_truncated', True), ('argv', ['different worker']),
                           ('cwd', str(self.root))]:
            process = copy.deepcopy(self.process); process[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.check(process)

    def test_process_costs_require_exact_finite_nonnegative_numbers_and_bound(self):
        for key in ('wall_seconds', 'cpu_seconds', 'monitor_cpu_seconds'):
            for value in (True, -1, float('nan'), float('inf'), placement.WORKER_SECONDS + .01):
                process = copy.deepcopy(self.process); process[key] = value
                with self.subTest(key=key, value=value), self.assertRaises((ValueError, pipeline.Rejected)):
                    self.check(process)

    def test_outer_cost_and_authority_corruption_refuse(self):
        for key, value in [('wall_seconds', True), ('full_cpu_seconds', -1), ('wall_seconds', float('nan')),
                           ('full_cpu_seconds', 119.01), ('schema', True), ('accepted', True), ('status', 'cancelled')]:
            outer = copy.deepcopy(self.outer); outer[key] = value
            with self.subTest(key=key), self.assertRaises((ValueError, pipeline.Rejected)):
                self.check(outer=outer)

    def test_late_evidence_bytes_or_identity_change_refuse(self):
        def mutate(): (self.output / 'work' / 'result.json').write_text('{"changed":true}')
        with self.assertRaises(ValueError): self.check(mutation=mutate)
        (self.output / 'work' / 'result.json').write_text('{}')
        def replace():
            work = self.output / 'work'; work.rename(self.output / 'preserved-old-work'); work.mkdir()
            (work / 'result.json').write_text('{}')
        with self.assertRaises(ValueError): self.check(mutation=replace)


class PublicationControls(unittest.TestCase):
    def account(self, record, remaining):
        tree = ast.parse(Path(placement.__file__).read_text())
        qualify = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'qualify')
        account = next(node for node in qualify.body if isinstance(node, ast.FunctionDef) and node.name == 'account')
        context = dict(record=record, elapsed_time=lambda: 2., started=0.,
                       h=SimpleNamespace(cpu_seconds=lambda: 1.), cpu_start=0., remaining=remaining)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[account], type_ignores=[])), placement.__file__, 'exec'), context)
        return context['account']

    def test_cancel_or_stale_final_publication_clears_pending_and_preserves_invalidated_receipt(self):
        for failure in (KeyboardInterrupt, ValueError):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary).resolve()
                record = dict(status='pending_candidate', placement_qualified=True, accepted=False)
                def fail(): raise failure('late failure')
                result = floor_route.publish(output, record, lambda: None, self.account(record, lambda: 90.),
                    lambda: 90., final_check=fail)
                self.assertIs(result['placement_qualified'], False)
                self.assertEqual(result['status'], 'cancelled' if failure is KeyboardInterrupt else 'invalidated')
                self.assertFalse(json.loads((output / 'result.json').read_text())['placement_qualified'])
                self.assertEqual(len(list(output.glob('invalidated-result-*.json'))), 1)

    def test_exhausted_publication_reserve_cannot_keep_positive_qualification(self):
        record = dict(status='pending_candidate', placement_qualified=True, accepted=False)
        self.account(record, lambda: .5)()
        self.assertEqual(record['status'], 'budget_exhausted'); self.assertIs(record['placement_qualified'], False)


class SourceGuardControls(unittest.TestCase):
    """A retained-check witness is test input, never a Native success claim."""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='placement-source-guard-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.runtime = self.root / 'runtime'; self.output = self.runtime / '.runs' / 'qualified'
        self.output.mkdir(parents=True)
        self.source = self.root / 'original' / 'owned.kicad_pcb'; self.source.parent.mkdir()
        self.source.write_text('original fixture')
        self.source.with_suffix('.kicad_prl').write_text('{}')
        self.binding = {'inspection': {'source': str(self.source)},
                        'intent': {'settings': {'schema': 1}}}  # Synthetic legacy preserve-all witness.
        work, boards = placement._paths(self.output, self.binding)
        for board in (*boards.values(), *(work / (name + '-input') / self.source.name
                                         for name in ('source-drc', 'final-drc'))):
            board.parent.mkdir(parents=True); board.write_text('candidate fixture')
            board.with_suffix('.kicad_prl').write_text('{}')
        self.candidate = boards['candidate']
        self.receipt = self.output / 'process.json'; self.receipt.write_text('{}')
        self.witness = dict(current=True, placement_qualified=True, evidence=str(self.output),
            candidate=str(self.candidate), binding=self.binding,
            evidence_hashes=placement.h.evidence_witness(self.output),
            **{name: False for name in placement.AUTHORITY})
        self.root_patch = patch.object(placement.c, 'ROOT', self.runtime); self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.material_patch = patch.object(placement, 'material'); self.material = self.material_patch.start()
        self.addCleanup(self.material_patch.stop)

    def guard(self, review=None):
        return placement.source_guard(self.output, self.witness, verify_review=review)

    def test_exact_checked_handoff_calls_no_native_and_cannot_gain_authority(self):
        with patch.object(placement, 'check', side_effect=AssertionError('no repeated full proof')):
            review = Mock(return_value=None); guard = self.guard(review)
            self.assertEqual(guard.board, self.candidate); self.assertIsNone(guard.check(self.candidate))
            self.assertGreaterEqual(review.call_count, 4)
            self.witness['accepted'] = True
            self.assertIsNone(guard.check(self.candidate))  # Captured witness is detached.
            with self.assertRaises(ValueError): self.guard()

    def test_reject_close_edit_or_authorizing_review_callback_blocks_handoff(self):
        review = Mock(return_value=None); guard = self.guard(review)
        for error in ('review rejected', 'review closed', 'pose edited', 'qualification cancelled'):
            review.side_effect = ValueError(error)
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                guard.check(self.candidate)
        review.side_effect = None; review.return_value = True
        with self.assertRaisesRegex(ValueError, 'no result authority'): guard.check(self.candidate)

    def test_candidate_or_retained_evidence_change_blocks_handoff(self):
        guard = self.guard(); self.receipt.write_text('{"changed":true}')
        with self.assertRaises(ValueError): guard.check(self.candidate)
        self.receipt.write_text('{}'); self.candidate.write_text('changed candidate')
        with self.assertRaises(ValueError): guard.check(self.candidate)

    def test_source_or_tool_changes_and_late_evidence_change_block_handoff(self):
        guard = self.guard()
        self.material.side_effect = ValueError('source or tools changed')
        with self.assertRaisesRegex(ValueError, 'source or tools changed'): guard.check(self.candidate)
        def late(_): self.receipt.write_text('{"changed":true}')
        self.material.side_effect = late
        with self.assertRaisesRegex(ValueError, 'changed during origin check'): guard.check(self.candidate)

    def test_actual_changed_prl_link_metadata_blocks_handoff(self):
        guard = self.guard()
        os.link(self.candidate.with_suffix('.kicad_prl'), self.root / 'owned-prl-link')
        with self.assertRaisesRegex(pipeline.Rejected, 'PRL retained current'):
            guard.check(self.candidate)


if __name__ == '__main__': unittest.main()
