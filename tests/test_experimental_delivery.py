"""Caller-context delivery controls with authored workers; never Native proof.

Reuse existing filesystem/process fixtures. Synthetic central routing readback
and its local-settings semantic seam are explicitly mocked for plumbing cases;
real bounded copies, receipt publication, process readers and PRL guards run.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import stat
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autorouter import config as c, floor_route as f, handoff as h
from autorouter import local_settings as ls, pipeline as p, review_export as e
from autorouter import review_view as view
from experiments.native_schematic_transport_v1 import fixture as owned
from tests import test_handoff as handoff_fixture
from tests import test_native_toolchain as tool_fixture
from tests import test_review_export as export_fixture
from tests import test_review_view as view_fixture


def authored_toolchain(root):
    """Pinned inert files, never executables or a claim about installed KiCad."""
    args = {'expected_version': '10.0.7'}
    for name in ('cli', 'python', 'pcbnew'):
        path = root / ('authored-' + name)
        path.write_text('authored never-executed delivery tool ' + name)
        args[name] = path; args[name + '_sha256'] = p.sha(path)
    return p.ExperimentalNativeToolchain(**args)


def experimental_report(data, nt, source):
    result = copy.deepcopy(data)
    result.update(scope='whole_board_unlocked_routing', adapter='none', baseline='B0',
                  engine_profile='standard', scoring_variant=None,
                  schematic_parity='checked by final native DRC',
                  source_hashes=p.tree_hash(source.parent), **p.experimental_route_record(nt, True))
    return result


class DeliveryAuthorityTests(unittest.TestCase):
    setUp = tool_fixture.NativeToolchainControls.setUp

    def test_only_typed_explicit_caller_context_can_authorize_delivery(self):
        nt = self.toolchain
        self.assertEqual(h.delivery_kwargs(), {})
        self.assertEqual(h.delivery_kwargs(nt, True), dict(native_toolchain=nt, experimental_schematic_parity=True))
        for tool, parity in ((nt, False), (None, True), (nt, 1), ({}, True)):
            with self.subTest(tool=type(tool), parity=parity), self.assertRaises(p.Rejected):
                h.delivery_kwargs(tool, parity)
        expected = {'native_delivery_context': p.experimental_route_record(nt, True)}
        h.check_delivery_context(expected, nt, True)
        for record in ({}, {'native_delivery_context': {}},
                       {'native_delivery_context': dict(expected['native_delivery_context'], production_admitted=0)}):
            with self.subTest(record=record), self.assertRaises(p.Rejected):
                h.check_delivery_context(record, nt, True)
        for record in (expected, {'native_delivery_context': None}, p.experimental_route_record(nt, True)):
            with self.subTest(default_record=record), self.assertRaises(p.Rejected):
                h.check_delivery_context(record)

    def test_receipt_cannot_select_another_caller_or_changed_tool(self):
        record = {'native_delivery_context': p.experimental_route_record(self.toolchain, True)}
        other_root = self.root / 'other'; other_root.mkdir()
        other = authored_toolchain(other_root)
        with self.assertRaises(p.Rejected): h.check_delivery_context(record, other, True)
        self.toolchain.cli.write_bytes(b'late tool drift')
        with self.assertRaisesRegex(p.Rejected, 'tool changed'):
            h.check_delivery_context(record, self.toolchain, True)


class DeliveryHandoffTests(unittest.TestCase):
    def setUp(self):
        handoff_fixture.ReviewCopyTests.setUp(self)
        self.nt = authored_toolchain(self.root)
        self.ctx = dict(native_toolchain=self.nt, experimental_schematic_parity=True)
        for directory in (self.source, self.candidate):
            (directory / 'board.kicad_sch').write_text('(kicad_sch (version 20250114))')
        self.data = experimental_report(self.data, self.nt, self.source / 'board.kicad_pcb')
        self.data.update(native={'opens': 0, 'blocking': 0, 'warnings': 0, 'exclusions': 0,
                                 'ignored_checks': [], 'findings': []}, metrics={'version': '10.0.7'})
        self.receipt.write_text(json.dumps(self.data))
        # The underlying route is synthetic. Only its established semantic guard
        # seam is mocked; the caller's actual tool-byte check still runs.
        guard = patch.object(p, 'check_experimental_local_settings',
                             side_effect=lambda folder, data, nt: nt.check())
        self.guard = guard.start(); self.addCleanup(guard.stop)

    def test_copy_choice_and_bind_propagate_context_without_claiming_approval(self):
        review = self.root / 'review'
        result = h.review_copy(self.receipt, review, **self.ctx)
        self.assertEqual(result['native_delivery_context'], p.experimental_route_record(self.nt, True))
        self.assertTrue(self.check.call_args_list)
        self.assertTrue(all(call.kwargs == self.ctx for call in self.check.call_args_list))
        choice = h.review_choice(review / 'review.json', self.root / 'choice', 'accept', **self.ctx)
        self.assertEqual(choice['native_delivery_context'], result['native_delivery_context'])
        self.assertFalse(choice['human_pcb_approval_observed']); self.assertFalse(choice['routing_accepted'])
        with patch.object(p, 'check_result', return_value=self.check.return_value) as central:
            binding, report = e.bind(self.root / 'choice/choice.json', **self.ctx)
        self.assertEqual(central.call_args.kwargs, self.ctx)
        self.assertEqual(binding['native_delivery_context'], result['native_delivery_context'])
        self.assertEqual(report, self.data)
        with self.assertRaises(p.Rejected): h.review_copy(self.receipt, self.root / 'default-review')
        with self.assertRaises(p.Rejected): h.review_choice(review / 'review.json', self.root / 'default-choice', 'accept')
        with self.assertRaises(p.Rejected): e.bind(self.root / 'choice/choice.json')

    def test_late_tool_check_source_byte_change_invalidates_published_review(self):
        target = self.root / 'late-review'; state = {'armed': False, 'mutated': False}
        save, check = h.save_json, p.ExperimentalNativeToolchain.check
        def publish(path, record):
            save(path, record)
            if path.name == 'review.json' and record.get('status') == 'ready_for_manual_review':
                state['armed'] = True
        def checked(nt):
            check(nt)
            if state['armed'] and not state['mutated']:
                source = self.source / 'board.kicad_pro'
                source.write_bytes(source.read_bytes() + b'\n'); state['mutated'] = True
        with patch.object(h, 'save_json', side_effect=publish), \
                patch.object(p.ExperimentalNativeToolchain, 'check', checked), self.assertRaises(p.Rejected):
            h.review_copy(self.receipt, target, **self.ctx)
        self.assertTrue(state['mutated'])
        current = f.read_json(target / 'review.json')
        self.assertNotEqual(current['status'], 'ready_for_manual_review')
        self.assertTrue(list(target.glob('invalidated-review-*')))


class DeliveryExportTests(unittest.TestCase):
    def setUp(self):
        export_fixture.ExportControls.setUp(self)
        self.nt = authored_toolchain(self.root)
        self.ctx = dict(native_toolchain=self.nt, experimental_schematic_parity=True)
        self.report_version = '10.0.7'; self.wrong_prefix = False
        project = json.loads(owned.project()); project['meta']['filename'] = 'board.kicad_pro'
        project['net_settings']['classes'][0]['track_width'] = .25
        for directory in (self.source, self.candidate):
            (directory / 'board.kicad_pro').write_text(json.dumps(project))
            (directory / 'board.kicad_sch').write_text('(kicad_sch (version 20250114))')
        self.metrics['version'] = '10.0.7'
        self.report = experimental_report(self.report, self.nt, self.source / 'board.kicad_pcb')
        self.report.update(metrics=self.metrics)
        p.save_json(self.receipt, self.report)
        self.stack.enter_context(patch.object(p, 'check_experimental_local_settings',
                                             side_effect=lambda folder, data, nt: nt.check()))
        h.review_copy(self.receipt, self.root / 'explicit-review', **self.ctx)
        self.choice = self.root / 'explicit-choice/choice.json'
        h.review_choice(self.root / 'explicit-review/review.json', self.choice.parent, 'accept', **self.ctx)
        self.output = self.root / 'explicit-export'

    def native_run(self, argv, *, cwd, log, **kwargs):
        if log.stem != 'final-netclasses':
            row = export_fixture.ExportControls.native_run(self, argv, cwd=cwd, log=log, **kwargs)
            if log.stem in ('refill-drc', 'final-drc'):
                target = Path(argv[argv.index('--output') + 1]); raw = json.loads(target.read_text())
                raw['kicad_version'] = self.report_version; target.write_text(json.dumps(raw))
                if '--schematic-parity' in argv:
                    log.write_bytes(b'Found 0 schematic parity issues\n')
                    row['log_bytes'] = log.stat().st_size
            return row
        self.calls.append((argv, kwargs)); log.write_bytes(b'')
        board = Path(argv[-2])
        mapping = dict(schema=1, native_version='10.0.7', units='integer nanometres',
            source=str(board), board_sha256=p.sha(board), project_sha256=p.sha(board.with_suffix('.kicad_pro')),
            board_saved=False, nets=[dict(name='SIG', netcode=1, **{'class': 'Default'}, width_nm=250000,
                clearance_nm=200000, via_diameter_nm=800000, via_drill_nm=400000, copper_pad_count=0)])
        Path(argv[-1]).write_text(json.dumps(mapping))
        actual = list(argv)
        if self.wrong_prefix: actual[len(f.SANDBOX)] = str(c.PYTHON)
        return dict(argv=actual, cwd=str(cwd), log=str(log), log_bytes=0, log_truncated=False,
                    status='success', exit_code=0, cleanup_complete=True,
                    wall_seconds=0., cpu_seconds=0., monitor_cpu_seconds=0.)

    def export(self):
        return e.export(self.choice, self.output, **self.ctx)

    def test_explicit_fresh_export_requires_default_class_map_and_exact_context(self):
        result = self.export()
        self.assertTrue(result['export_accepted'])
        self.assertEqual([Path(row[0][-1]).name for row in self.calls],
                         ['board.kicad_pcb', 'final-netclasses.json', 'board.kicad_pcb', 'metrics.json'])
        checked = e.check_export(self.output / 'export.json', **self.ctx)
        self.assertTrue(checked['current'])
        with self.assertRaises(p.Rejected): e.check_export(self.output / 'export.json')
        path = self.output / 'export.json'; data = f.read_json(path)
        # Strip the entire Default-only map/step, and honestly recompute the outer
        # file witness. The stage reader must still demand the missing proof.
        for name in ('final-netclasses.json', 'final-netclass-audit.json', 'final-netclasses-process.json', 'final-netclasses.log'):
            (self.output / 'validation' / name).unlink()
        data['steps'] = [step for step in data['steps'] if step['name'] != 'final-netclasses']
        data['export_evidence'] = e.evidence(self.output); path.write_text(json.dumps(data))
        with self.assertRaises((p.Rejected, FileNotFoundError)):
            e.check_export(path, **self.ctx)

    def test_wrong_native_version_or_worker_prefix_never_exports(self):
        self.report_version = '10.0.0'
        with self.assertRaises(p.Rejected): self.export()
        export_fixture.ExportControls.no_positive(self)
        self.report_version = '10.0.7'; self.wrong_prefix = True
        self.output = self.root / 'wrong-prefix-export'
        with self.assertRaises(p.Rejected): self.export()
        export_fixture.ExportControls.no_positive(self)

    def test_experimental_pour_scope_refuses_before_any_worker(self):
        binding, report = e.bind(self.choice, **self.ctx)
        with patch('autorouter.pour_rule_area.qualify', return_value=[{'authored': 'unsupported intent'}]), \
                self.assertRaisesRegex(p.Rejected, 'ordinary native zones'):
            e.lineage(binding, report, **self.ctx)
        self.assertEqual(self.calls, [])


class DeliveryPreviewTests(unittest.TestCase):
    setUp = tool_fixture.NativeToolchainControls.setUp

    def rendered(self):
        base = self.root / 'plots'; base.mkdir()
        source, candidate, out, _ = view_fixture.PlotCopyControls.projects(self, base, old_prl=True)
        shutil.copytree(source, out / 'before'); shutil.copytree(candidate, out / 'project')
        calls = []
        worker = view_fixture.PlotCopyControls.plot_worker(self, out / 'before', out / 'project',
                                                         lambda *args: None, calls)
        ctx = dict(native_toolchain=self.toolchain, experimental_schematic_parity=True)
        with patch.object(p, 'run', side_effect=worker):
            preview = view.render(out, out / 'before/board.kicad_pcb', out / 'project/board.kicad_pcb',
                                  {}, lambda: 30, lambda: None, **ctx)
        self.assertEqual(len(calls), 4)
        return out, preview

    def test_exact_caller_plot_process_and_context_replay(self):
        out, preview = self.rendered()
        self.assertEqual(len(view.check_experimental_preview(out, preview, self.toolchain, True)), 4)
        with self.assertRaises(p.Rejected): view.check_experimental_preview(out, preview)
        missing = copy.deepcopy(preview); missing.pop('native_delivery_context')
        with self.assertRaises(p.Rejected): view.check_experimental_preview(out, missing, self.toolchain, True)
        path = out / 'plot-work/before-F.Cu-process.json'; row = f.read_json(path)
        row['argv'][len(f.SANDBOX)] = str(c.CLI); path.write_text(json.dumps(row))
        preview['steps'][0] = row
        with self.assertRaises(p.Rejected): view.check_experimental_preview(out, preview, self.toolchain, True)

    def test_missing_preview_proof_file_is_not_a_current_preview(self):
        out, preview = self.rendered()
        required = ('preview.html', 'plot-work/before-F.Cu-input-binding.json',
                    'plot-work/after-B.Cu-process.json', 'plot-work/native-plots/after-F.Cu.svg',
                    'plot-work/plots/before-B.Cu.svg', 'plot-work/before-F.Cu-input/board.kicad_pro')
        for name in required:
            changed = copy.deepcopy(preview); changed['files'].pop(name)
            with self.subTest(missing=name), self.assertRaisesRegex(p.Rejected, 'file census'):
                view.check_experimental_preview(out, changed, self.toolchain, True)

    @unittest.skipUnless(sys.platform == 'darwin' and hasattr(os, 'chflags'), 'actual Mac flags required')
    def test_additional_export_check_cannot_hide_late_plot_prl_flag(self):
        out, preview = self.rendered()
        prl = out / 'plot-work/before-F.Cu-input/board.kicad_prl'
        extra = self.root / 'additional'; extra.mkdir()
        def semantic(folder, data, nt):
            nt.check()
            if Path(folder) == extra: os.chflags(prl, stat.UF_IMMUTABLE, follow_symlinks=False)
        try:
            with patch.object(p, 'check_experimental_local_settings', side_effect=semantic), \
                    self.assertRaises(p.Rejected):
                h.delivery_guards(self.root / 'route/result.json', {'steps': []}, self.toolchain,
                                  preview, out, additional=((extra, {'steps': []}),))
        finally:
            if prl.exists() and prl.stat().st_flags: os.chflags(prl, 0, follow_symlinks=False)


class BareSourcePrlReplayTests(unittest.TestCase):
    setUp = tool_fixture.NativeToolchainControls.setUp

    @unittest.skipUnless(sys.platform == 'darwin' and hasattr(os, 'chflags'), 'actual Mac flags required')
    def test_additional_export_callback_cannot_hide_bare_source_refill_prl_flag(self):
        job = p.Job(self.root / 'source-journal', 30, native_toolchain=self.toolchain,
                    experimental_schematic_parity=True, protect_local_settings=True)
        work = job.out / 'refill'; work.mkdir()
        board = work / 'board.kicad_pcb'; board.write_text('(kicad_pcb)')
        board.with_suffix('.kicad_pro').write_text('{}')
        prl = board.with_suffix('.kicad_prl'); prl.write_text('{"owned":"source PRL"}')
        seam = SimpleNamespace(calls=[], native_mode='valid', warning={
            'type': 'lib_footprint_mismatch', 'severity': 'warning', 'description': 'authored seam', 'items': []})
        def worker(argv, *, cwd, log, **kwargs):
            row = export_fixture.ExportControls.native_run(seam, argv, cwd=cwd, log=log, **kwargs)
            path = Path(argv[argv.index('--output') + 1]); raw = json.loads(path.read_text())
            raw['kicad_version'] = '10.0.7'; path.write_text(json.dumps(raw))
            return row
        with patch.object(p, 'run', side_effect=worker): job.drc('refill-drc', board, save=True)
        self.assertEqual(job.steps[0]['argv'][:3], [str(self.toolchain.cli), 'pcb', 'drc'])
        data = {'steps': job.steps, 'native': {'findings': []}}
        extra = self.root / 'export-packet'; extra.mkdir()
        def semantic(folder, report, nt):
            nt.check()
            if Path(folder) == extra: os.chflags(prl, stat.UF_IMMUTABLE, follow_symlinks=False)
        try:
            with patch.object(p, 'check_experimental_local_settings', side_effect=semantic), \
                    self.assertRaises(p.Rejected):
                h.delivery_guards(job.out / 'result.json', data, self.toolchain,
                                  additional=((extra, {'steps': []}),))
        finally:
            if prl.exists() and prl.stat().st_flags: os.chflags(prl, 0, follow_symlinks=False)


if __name__ == '__main__': unittest.main()
