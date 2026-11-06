"""Pure dispatch/publication boundaries for composed placement routing.

Native proof/engine execution is deliberately absent. Mocked successful stage
proofs isolate mandatory lineage enforcement; they are never Native evidence.
"""
from contextlib import ExitStack
import copy
import datetime
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from autorouter import floor_route as f, pipeline as p, placement, preferences as pref, review_export as export
from experiments.placement_native_proposal_v1 import ordinary_fixture


def effective(seconds=90):
    return pref.validate(dict(pref.DEFAULTS, scope='selected_nets', nets=['ROUTE_A', 'ROUTE_B'],
                              profile='completion-only', seconds=seconds))


def captured(value):
    return dict(started=time.monotonic(), parent_cpu=time.process_time(), child_cpu=f.child_cpu(),
                started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                captured=None, effective=value, snapshot=pref.snapshot(None, value_without_schema(value)))


def value_without_schema(value):
    return {key: item for key, item in value.items() if key != 'schema'}


class PlacementOriginPolicy(unittest.TestCase):
    """Native-policy recognition is distinct from full placement qualification."""
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='placement-origin-policy-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name).resolve()
        self.folder = self.root / 'route'; self.folder.mkdir()
        self.qualification = self.root / 'unverified'; self.qualification.mkdir()
        self.marker = self.folder / placement.ORIGIN_FILE
        self.descriptor = dict(schema=1, kind=placement.ORIGIN_KIND, qualification=str(self.qualification),
            result_sha256='1'*64, binding_sha256='2'*64, evidence_sha256='3'*64)
        self.report = dict(schema=1, scope='selected_nets', placement_origin=self.descriptor)
        self.write()

    def write(self):
        self.marker.write_text(json.dumps(self.descriptor))

    def test_exact_origin_uses_native_policy_but_still_needs_full_qualification(self):
        with patch.object(placement, 'check', side_effect=ValueError('unverified Native qualification')) as check:
            self.assertEqual(f.receipt_policy(self.report, self.folder), 'native')
            self.assertEqual(f.evidence_markers(self.folder), {'reviewed-placement-origin'})
            self.assertEqual(f.evidence_inventory(self.folder), p.tree_hash(self.folder))
            check.assert_not_called()
            with self.assertRaisesRegex(ValueError, 'unverified Native qualification'):
                placement.check_routing_record(self.folder, self.report)
            check.assert_called_once_with(self.qualification)
        self.assertNotIn('accepted', self.report)

    def test_missing_pair_and_nonregular_marker_refuse(self):
        with self.assertRaises(ValueError): f.receipt_policy({'schema': 1}, self.folder)
        self.marker.unlink()
        with self.assertRaises(ValueError): f.receipt_policy(self.report, self.folder)
        self.marker.mkdir()
        with self.assertRaises((ValueError, p.Rejected)): f.receipt_policy(self.report, self.folder)
        self.marker.rmdir(); self.marker.symlink_to(self.root/'absent')
        with self.assertRaises((ValueError, p.Rejected)): f.receipt_policy(self.report, self.folder)

    def test_descriptor_types_json_and_bound_marker_cannot_downgrade(self):
        for key, value in (('schema', True), ('kind', 'legacy'), ('qualification', None),
                           ('qualification', 'relative'), ('result_sha256', 1),
                           ('binding_sha256', 'A'*64), ('evidence_sha256', 'short')):
            old = self.descriptor[key]; self.descriptor[key] = value; self.write()
            with self.subTest(key=key, value=value), self.assertRaises((ValueError, p.Rejected)):
                f.receipt_policy(self.report, self.folder)
            self.descriptor[key] = old
        self.write(); raw = self.marker.read_text()
        for changed in (raw[:-1]+',"schema":1}', raw[:-1]+',"extra":NaN}', '{}'):
            self.marker.write_text(changed)
            with self.subTest(changed=changed), self.assertRaises((ValueError, p.Rejected)):
                f.receipt_policy(self.report, self.folder)

    def test_all_other_legacy_markers_and_claims_still_refuse(self):
        for name in ('placement-policy.json', 'placement-search.json', 'placement-unknown',
                     'planning-unknown', 'floor-policy.json'):
            path = self.folder/name; path.write_text('{}')
            with self.subTest(name=name), self.assertRaises(p.Rejected):
                f.receipt_policy(self.report, self.folder)
            path.unlink()
        for key in ('placement_policy', 'placement_unknown', 'planning_parameters',
                    'floor_policy', 'guidance_policy'):
            with self.subTest(key=key), self.assertRaises(p.Rejected):
                f.receipt_policy(dict(self.report, **{key: None}), self.folder)
        for value in (True, 3, 4, 5):
            with self.subTest(schema=value), self.assertRaises(ValueError):
                f.receipt_policy(dict(self.report, schema=value), self.folder)


class PlacementRouteDispatch(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='placement-route-lineage-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name).resolve()
        self.board = ordinary_fixture.write_project(self.root / 'original')
        self.output = self.root / 'new-route'; self.origin = self.root / 'qualification'

    def test_public_route_forwards_origin_but_legacy_call_has_no_new_dispatch_key(self):
        for origin in (None, self.origin):
            with self.subTest(origin=origin), patch.object(p, '_route', return_value={'pending': True}) as inner:
                self.assertEqual(p.route(self.board, self.output, placement_origin=origin), {'pending': True})
                if origin is None: self.assertNotIn('placement_origin', inner.call_args.kwargs)
                else: self.assertEqual(inner.call_args.kwargs['placement_origin'], origin)

    def test_raw_or_mixed_execution_authority_refuses_before_binding_and_work(self):
        cases = [{}, {'native_toolchain': object()}, {'comparison_context': object()},
                 {'experimental_schematic_parity': True}, {'_improve_context': object()},
                 {'_improve_budget': object()}, {'guidance_policy': 'board-floors-v1'},
                 {'_fanout_enabled': False}, {'_optimizer_enabled': False},
                 {'_engine_clearance_margin_nm': 20000}, {'_engine_global_width_policy': 'extra'}]
        for case in cases:
            kwargs = dict(case)
            if case: kwargs['preference_overrides'] = value_without_schema(effective())
            with self.subTest(case=case), patch.object(placement, 'bind_routing') as bind, \
                    patch.object(p, 'Job') as job, self.assertRaisesRegex(p.Rejected, 'placement origin requires'):
                p._route(self.board, self.output, placement_origin=self.origin, **kwargs)
            bind.assert_not_called(); job.assert_not_called(); self.assertFalse(self.output.exists())

    def test_preference_recursion_keeps_origin_and_full_captured_settings(self):
        value = effective(75)
        with patch.object(p, 'route', return_value={'stub': True}) as recurse:
            result = p._route(self.board, self.output, preference_overrides=value_without_schema(value),
                              placement_origin=self.origin)
        self.assertEqual(result, {'stub': True})
        call = recurse.call_args.kwargs
        self.assertEqual(call['placement_origin'], self.origin)
        self.assertEqual(call['_preferences']['effective'], value)
        self.assertEqual(pref.readback(call['_preferences']['snapshot']), value)
        self.assertLessEqual(call['_preferences']['started'], time.monotonic())
        self.assertEqual(call['seconds'], 75); self.assertEqual(call['engine_profile'], 'completion-only')

    def intake(self, request, bind):
        stack = ExitStack(); self.addCleanup(stack.close)
        stack.enter_context(patch.object(p.c, 'NATIVE_VERSION', '10.0.7'))
        stack.enter_context(patch.object(p, 'check_native7_selected_source'))
        bound = stack.enter_context(patch.object(placement, 'bind_routing', side_effect=bind))
        job = stack.enter_context(patch.object(p, 'Job'))
        storage = stack.enter_context(patch.object(p, 'check_storage'))
        return bound, job, storage

    def test_stale_origin_refuses_before_native_output_or_storage_allocation(self):
        value = effective(); request = captured(value)
        def reject(*_, **__): raise ValueError('qualification source changed')
        bound, job, storage = self.intake(request, reject)
        with self.assertRaisesRegex(ValueError, 'qualification source changed'):
            p._route(self.board, self.output, **pref.route_arguments(value), _preferences=request,
                     placement_origin=self.origin)
        bound.assert_called_once_with(self.origin, self.board, value, method='route')
        job.assert_not_called(); storage.assert_not_called(); self.assertFalse(self.output.exists())

    def test_origin_readback_cost_is_inside_budget_and_cannot_start_late_job(self):
        value = effective(5); request = captured(value); clock = [request['started']]
        def expensive(*_, **__): clock[0] += 6; return {'synthetic': 'origin'}
        _, job, storage = self.intake(request, expensive)
        with patch.object(p.time, 'monotonic', side_effect=lambda: clock[0]), \
                self.assertRaisesRegex(p.Rejected, 'budget exhausted while checking placement origin'):
            p._route(self.board, self.output, **pref.route_arguments(value), _preferences=request,
                     placement_origin=self.origin)
        job.assert_not_called(); storage.assert_not_called(); self.assertFalse(self.output.exists())

    def test_marker_and_report_are_captured_before_first_native_stage(self):
        value = effective(); request = captured(value)
        descriptor = dict(schema=1, kind='test-origin', qualification=str(self.origin))
        class NoNativeJob:
            def __init__(self, folder, *_args, **_kwargs):
                folder.mkdir(); self.steps = []
            def remaining(self): return 80
            def native(self, *_args, **_kwargs): raise AssertionError('No Native in this test')
        def stop(*_args, **_kwargs): raise p.Rejected('intentional stop before Native')
        def publish(_output, record, stable, account, _remaining, **_kwargs):
            stable(); account(); return copy.deepcopy(record)
        with patch.object(p.c, 'NATIVE_VERSION', '10.0.7'), patch.object(p, 'check_native7_selected_source'), \
                patch.object(placement, 'bind_routing', return_value=descriptor), \
                patch.object(p, 'Job', NoNativeJob), patch.object(p, 'check_storage'), \
                patch.object(p, 'sha', return_value=p.c.JAR_SHA256), patch.object(p, 'tool_manifest', return_value={}), \
                patch.object(p.shutil, 'copy2'), patch.object(p, 'preflight', side_effect=stop), \
                patch.object(f, 'publish', side_effect=publish):
            result = p._route(self.board, self.output, **pref.route_arguments(value), _preferences=request,
                              placement_origin=self.origin)
        self.assertIs(result['accepted'], False)
        self.assertIn('intentional stop before Native', result['reason'])
        self.assertEqual(result['placement_origin'], descriptor)
        self.assertEqual(json.loads((self.output / 'placement-origin.json').read_text()), descriptor)
        self.assertEqual(result['routing_preferences']['effective'], value)
        self.assertEqual(result['steps'], [])
        self.assertFalse((self.output / 'candidate').exists())


class PlacementReadbackCache(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='placement-origin-cache-')
        self.addCleanup(temporary.cleanup); self.folder = Path(temporary.name).resolve()
        self.path = self.folder / 'result.json'; self.marker = self.folder / 'placement-origin.json'
        self.state = {'entries': {}, 'native7_contexts': {}}
        token = p._readback_session.set(self.state); self.addCleanup(p._readback_session.reset, token)

    def check(self, reader):
        with patch.object(p.c, 'current_native_selection'), patch.object(p, 'experimental_route_record'), \
                patch.object(p, '_check_result_uncached', side_effect=reader) as full, \
                patch.object(p, '_readback_witness', side_effect=AssertionError('Origin is not covered by ordinary cache')):
            result = p.check_result(self.path)
        return result, full.call_count

    def test_field_marker_or_dangling_marker_always_bypasses_ordinary_cache(self):
        for mode in ('field', 'marker', 'dangling_marker'):
            data = dict(schema=1, accepted=True, status='routing_accepted')
            if mode == 'field': data['placement_origin'] = {'untrusted': True}
            elif mode == 'marker': self.marker.write_text('{}')
            else: self.marker.symlink_to(self.folder / 'absent-target')
            self.path.write_text(json.dumps(data))
            try:
                result, calls = self.check(lambda *_args, **_kwargs: {'only_dispatch_test': True})
                self.assertEqual(result, {'only_dispatch_test': True}); self.assertEqual(calls, 1)
            finally:
                if self.marker.exists() or self.marker.is_symlink(): self.marker.unlink()

    def test_second_read_cannot_reuse_result_after_origin_changed(self):
        self.path.write_text(json.dumps(dict(schema=1, accepted=True, status='routing_accepted',
                                            placement_origin={'untrusted': True})))
        calls = []
        def full(*_args, **_kwargs):
            calls.append(True)
            if len(calls) > 1: raise p.Rejected('changed original qualification')
            return {'only_dispatch_test': True}
        self.check(full)
        with self.assertRaisesRegex(p.Rejected, 'changed original qualification'): self.check(full)
        self.assertEqual(len(calls), 2)


class PlacementExportLineage(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='placement-export-lineage-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name).resolve()
        self.route = self.root / 'route'; self.route.mkdir()
        self.final = self.root / 'fresh-export.kicad_pcb'; self.final.write_bytes(b'unit fixture only')
        self.binding = dict(receipt=str(self.route / 'result.json'))
        self.data = {'native': {'findings': []}}; self.report = {'native': {'findings': []}}

    def stage(self):
        # The Native stage proof is a stub solely to reach the shared lineage
        # boundary. Never interpret a return here as Native qualification.
        with patch.object(export, '_check_stage_proof', return_value=self.final):
            return export.check_stage(self.root, self.data, self.binding, self.report, None, None, None)

    def test_export_stage_checks_actual_final_candidate_against_parent_origin(self):
        self.report['placement_origin'] = {'unit': True}
        with patch.object(placement, 'check_routing_record', return_value={'audit_passed': True}) as checker:
            self.assertEqual(self.stage(), self.final)
        checker.assert_called_once_with(self.route, self.report, self.final)

    def test_missing_origin_field_or_marker_refuses_even_after_native_proof_stub(self):
        for mode in ('field_only', 'marker_only'):
            if mode == 'field_only': self.report['placement_origin'] = {}
            else:
                self.report.pop('placement_origin', None)
                (self.route / 'placement-origin.json').write_text('{}')
            with self.subTest(mode=mode), patch.object(placement, 'check') as qualification, \
                    self.assertRaisesRegex(ValueError, 'field/marker is missing'):
                self.stage()
            qualification.assert_not_called()

    def test_ordinary_export_has_no_qualification_dependency(self):
        with patch.object(placement, 'check', side_effect=AssertionError('No origin on ordinary route')):
            self.assertEqual(self.stage(), self.final)


if __name__ == '__main__': unittest.main()
