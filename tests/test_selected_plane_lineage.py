"""Constructed journal controls: NO Native execution or final DRC proof.

Only the final Native Default reader is stubbed for replay: this source fixture
has no full schematic/Native geometry. Real pure Default transforms, source
selection binding, export process checker and both adapter hooks still run.
"""
import copy
from contextlib import contextmanager
from decimal import Decimal, localcontext
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from autorouter import adapter, default_targets, floor_route, native_edge, pipeline as p
from autorouter import pour_rule_area, routing_scope as rs, selected_plane_transport as transport, sexpr as sx
from tests import test_default_targets as defaults


ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


@contextmanager
def fixture(*, complete=True):
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as temporary, \
            patch.object(p.c, 'NATIVE_VERSION', '10.0.7'), \
            patch.object(pour_rule_area, 'qualify', return_value=[]):
        root = Path(temporary)
        for name in ('snapshot', 'candidate', 'code'): (root/name).mkdir()
        source = root/'snapshot/board.kicad_pcb'; candidate = root/'candidate/board.kicad_pcb'
        raw, mapping, project, original = defaults.fixtures()
        original.append(['zone', ['net', '"DATA"'], ['layer', '"B.Cu"'],
                         ['polygon', ['pts', ['xy', '4', '4'], ['xy', '5', '4'], ['xy', '5', '5']]]])
        source.write_text(sx.dump(original) + '\n')
        names = ['RETURN']; task = p.routing_task(original, 'selected_nets', names)
        mapping['source'] = str(candidate)
        raw, mapping, project_raw, task_raw = defaults.inputs(raw, mapping, project, task)
        source.with_suffix('.kicad_pro').write_bytes(project_raw)
        candidate.write_bytes(task_raw); candidate.with_suffix('.kicad_pro').write_bytes(project_raw)
        (root/'native.dsn').write_bytes(raw); save(root/'export-netclasses.json', mapping)
        base, derivation = default_targets.transform(raw, mapping, project_raw, task_raw, source=str(candidate))
        (root/'default-targets.dsn').write_bytes(base); save(root/'default-targets.json', derivation)
        pins = {}
        for name in ('pipeline.py', 'adapter.py', 'selected_plane_transport.py'):
            (root/'code'/name).write_bytes((ROOT/'autorouter'/name).read_bytes())
            pins['autorouter/'+name] = p.sha(root/'code'/name)
        before_code = sorted(path.name for path in (root/'code').iterdir())
        transport.snapshot_policy(root)
        assert sorted(path.name for path in (root/'code').iterdir()) == before_code
        assert not (root/'code'/transport.POLICY_SNAPSHOT).exists()
        argv = [*p.native_prefix(), 'export', str(candidate), str(root/'task.dsn'),
                str(root/'export-netclasses.json'), '--task-copper-fixed']
        process = dict(name='export', argv=argv, cwd=str(root), exit_code=0, status='success', cleanup_complete=True)
        save(root/'export-process.json', process)
        data = dict(schema=1, source=str(source), input_policy='native', scope='selected_nets', adapter='both',
            tools=dict(kicad='10.0.7', implementation_sha256=pins), source_hashes=p.tree_hash(source.parent),
            task_sha256=p.sha(candidate), native_dsn_sha256=p.sha(root/'native.dsn'),
            routing_preferences=dict(effective=dict(schema=1, scope='selected_nets', nets=names, seconds=90,
                adapter='both', profile='completion-only', guidance='native', layers='source_all', scoring_preference=None)),
            selected_net_binding=rs.bind(source.read_bytes(), names), steps=[copy.deepcopy(process)],
            default_target_transport=dict(policy=p.DEFAULT_TARGET_ADMISSION_POLICY, file='default-targets.json',
                                          sha256=p.sha(root/'default-targets.json')),
            selected_plane_choice=dict(policy=transport.CHOICE_POLICY, mode=transport.VARIANT))
        assert 'selected_net_audit' not in data and 'selected_dsn_binding' not in data
        payload, binding = transport.capture(root, data, base)
        data['selected_plane_transport'] = binding
        if complete:
            adapted, record = adapter.adapt_bytes(base, 'both', [], plane_transport=payload)
            data['adapter_transformations'] = record
            (root/'edge-adapter-input.dsn').write_bytes(adapted)
            corrected, edge = native_edge.correct(adapted, p.native_edge_context(source))
            data['native_edge_correction'] = edge; save(root/'native-edge-correction.json', edge)
            (root/'routing-scope-input.dsn').write_bytes(corrected)
            emitted, data['selected_dsn_binding'] = rs.partition_dsn(corrected, names)
            (root/'task.dsn').write_bytes(emitted); save(root/'obstacles.json', [])
            data['selected_net_audit'] = rs.audit(original, original, names)
        yield root, data, base, payload


class SelectedPlaneLineageTests(unittest.TestCase):
    def test_experimental_flag_rejects_unknown_and_mixed_authorities_before_job(self):
        with patch.object(p, 'Job', side_effect=AssertionError('no job may start')) as job:
            for value in (True, False, 1, '', 'unknown'):
                with self.subTest(value=value), self.assertRaisesRegex(p.Rejected, 'experimental selected-plane policy'):
                    p._route('unused-source', 'unused-output', _selected_plane_policy=value)
            for key in ('native_toolchain', 'comparison_context', '_improve_context',
                        '_improve_budget', '_fanout_enabled', '_optimizer_enabled',
                        '_engine_clearance_margin_nm', '_engine_global_width_policy', 'placement_origin'):
                with self.subTest(key=key), self.assertRaisesRegex(p.Rejected, 'cannot mix authorities'):
                    p._route('unused-source', 'unused-output', _selected_plane_policy=transport.VARIANT, **{key: object()})
            job.assert_not_called()

    def test_private_flag_survives_preference_capture_without_starting_job(self):
        overrides = dict(scope='selected_nets', nets=['DATA'], profile='completion-only',
                         adapter='both', seconds=90)
        with patch.object(p, 'route', return_value='captured') as nested, \
                patch.object(p, 'Job', side_effect=AssertionError('capture only')) as job:
            self.assertEqual(p._route('unused-source', 'unused-output', preference_overrides=overrides,
                                     _selected_plane_policy=transport.VARIANT), 'captured')
            self.assertEqual(nested.call_args.kwargs['_selected_plane_policy'], transport.VARIANT)
            self.assertEqual(nested.call_args.kwargs['_preferences']['effective']['nets'], ['DATA'])
            job.assert_not_called()

    def test_policy_snapshot_is_exclusive_and_outside_canonical_code(self):
        with fixture(complete=False) as (root, data, base, payload):
            before = (root/transport.POLICY_SNAPSHOT).read_bytes()
            self.assertFalse((root/'code'/transport.POLICY_SNAPSHOT).exists())
            with self.assertRaises(FileExistsError): transport.snapshot_policy(root)
            self.assertEqual((root/transport.POLICY_SNAPSHOT).read_bytes(), before)
            self.assertEqual(set(path.name for path in (root/'code').iterdir()),
                             {Path(name).name for name in data['tools']['implementation_sha256']})

    def test_exact_decimal_policy_identity_changes_without_context_rounding(self):
        module = SimpleNamespace(__name__='constructed_policy', LIMIT=Decimal('2000000'))
        before = p._readback_live_identity((module,))
        with localcontext() as context:
            context.prec = 1
            module.LIMIT = Decimal('2000000.000000001')
            after = p._readback_live_identity((module,))
        self.assertNotEqual(before, after)
        self.assertEqual(after, p._readback_live_identity((module,)))
        class UnsupportedDecimal(Decimal):
            def as_tuple(self): raise AssertionError('subclass hook must not run')
        module.LIMIT = UnsupportedDecimal('1')
        with self.assertRaisesRegex(p.Rejected, 'unsupported mutable'):
            p._readback_live_identity((module,))

    def replay(self, root, data, base):
        # This one boundary lacks real Native/full-schematic evidence. _derive
        # still performs the real pure transform and actual process_check.
        with patch.object(p, 'check_default_target_transport', return_value={'constructed_test_boundary': True}):
            return transport.replay(root, data, base)

    def test_producer_capture_precedes_final_selected_audit_and_has_no_native_authority(self):
        with patch.object(p, 'check_default_target_transport', side_effect=AssertionError('Final proof does not exist yet')), \
                fixture(complete=False) as (root, data, base, payload):
            self.assertNotIn('selected_net_audit', data); self.assertNotIn('selected_dsn_binding', data)
            record = json.loads((root/transport.FILE).read_text())
            self.assertEqual(record['context']['planes'][0]['action'], 'retain')
            self.assertEqual(record['context']['planes'][0]['net_name'], 'DATA')
            for key in ('native_fill_equivalence', 'routing_accepted', 'approval_granted'): self.assertIs(record[key], False)
            floor_route.process_check(root, data, 'export', data['steps'][0]['argv'])
            self.assertEqual(payload['context'], record['context'])

    def test_final_replay_requires_central_selected_proofs_and_fresh_default_reader(self):
        with fixture() as (root, data, base, payload):
            self.assertEqual(self.replay(root, data, base), payload)
            for key in ('selected_net_audit', 'selected_dsn_binding'):
                bad = copy.deepcopy(data); bad.pop(key)
                with self.subTest(key=key), self.assertRaisesRegex(p.Rejected, 'missing selected-net'):
                    self.replay(root, bad, base)
            with patch.object(p, 'check_default_target_transport', return_value=None), \
                    self.assertRaisesRegex(p.Rejected, 'final Native Default'):
                transport.replay(root, data, base)

    def test_actual_map_process_base_Default_and_helper_changes_refuse(self):
        for fault in ('map', 'process', 'base', 'Defaultpin', 'helper', 'adapter', 'source-hash', 'selection', 'task', 'Nativehash'):
            with self.subTest(fault=fault), fixture() as (root, data, base, payload):
                if fault == 'map':
                    value=json.loads((root/'export-netclasses.json').read_text()); value['board_sha256']='0'*64; save(root/'export-netclasses.json',value)
                elif fault == 'process':
                    value=json.loads((root/'export-process.json').read_text()); value['exit_code']=1; save(root/'export-process.json',value); data['steps']=[value]
                elif fault == 'base': base += b'\n'
                elif fault == 'Defaultpin': data['default_target_transport']['sha256']='0'*64
                elif fault == 'helper': (root/transport.POLICY_SNAPSHOT).write_bytes(b'changed')
                elif fault == 'adapter': (root/'code/adapter.py').write_bytes(b'changed')
                elif fault == 'source-hash': data['source_hashes']['board.kicad_pcb']='0'*64
                elif fault == 'selection': data['routing_preferences']['effective']['nets']=['DATA']
                elif fault=='task': data['task_sha256']='0'*64
                else: data['native_dsn_sha256']='0'*64
                with self.assertRaises((p.Rejected, ValueError)): self.replay(root, data, base)

    def test_context_changed_even_after_rehash_refuses_in_each_real_hook(self):
        for hook in ('edge', 'pour'):
            with self.subTest(hook=hook), fixture() as (root, data, base, payload):
                record=json.loads((root/transport.FILE).read_text());record['context']['planes'][0]['action']='omit';save(root/transport.FILE,record)
                data['selected_plane_transport']['sha256']=p.sha(root/transport.FILE)
                with patch.object(p, 'check_default_target_transport', return_value={'constructed_test_boundary': True}), \
                        self.assertRaisesRegex(p.Rejected, 'selected plane transport: missing, changed or downgraded'):
                    if hook=='edge': p.check_native_edge_transport(root,data)
                    else: p.check_pour_evidence(root,data,sx.read(root/'snapshot/board.kicad_pcb'),root/'candidate/board.kicad_pcb')

    def test_missing_choice_deleted_evidence_and_baseline_downgrade_cannot_hide_variant(self):
        for fault in ('choice', 'proof', 'proof-and-choice', 'downgrade'):
            with self.subTest(fault=fault), fixture() as (root, data, base, payload):
                if fault in ('choice', 'proof-and-choice'): data.pop('selected_plane_choice')
                if fault in ('proof', 'proof-and-choice'): (root/transport.FILE).unlink()
                if fault=='downgrade': data['selected_plane_choice']['mode']=transport.BASELINE
                with self.assertRaises((p.Rejected, FileNotFoundError)): self.replay(root,data,base)
        # Even when every variant marker is deleted, the new captured producer
        # still requires its explicit baseline/variant choice.
        with fixture() as (root,data,base,payload):
            data.pop('selected_plane_choice');data.pop('selected_plane_transport');data['adapter_transformations'].pop('plane_transport');(root/transport.FILE).unlink()
            with self.assertRaisesRegex(p.Rejected,'explicit producer choice'):transport.choice(root,data)

    def test_captured_producer_capability_and_snapshot_source_cannot_be_laundered(self):
        for fault in ('producer-hash','missing-capability','dynamic-capability','Default-capability',
                      'selected-Default-capability','snapshot','source-name'):
            with self.subTest(fault=fault),fixture() as(root,data,base,payload):
                path=root/'code/pipeline.py'
                if fault=='producer-hash':path.write_bytes(path.read_bytes()+b'\n')
                elif fault in ('missing-capability','dynamic-capability','Default-capability','selected-Default-capability'):
                    text=path.read_text()
                    key = ('DEFAULT_TARGET_ADMISSION_POLICY' if fault=='Default-capability' else
                           'NATIVE7_SELECTED_DEFAULT_POLICY' if fault=='selected-Default-capability' else 'SELECTED_PLANE_CHOICE_POLICY')
                    needle=next(line for line in text.splitlines() if line.startswith(key+'='))
                    self.assertIn(needle,text)
                    text=text.replace(needle,"SELECTED_PLANE_CHOICE_POLICY='native7-selected-plane-'+'choice-v1'" if fault=='dynamic-capability' else '',1)
                    path.write_text(text);data['tools']['implementation_sha256']['autorouter/pipeline.py']=p.sha(path)
                elif fault=='snapshot':(root/'snapshot/board.kicad_pcb').write_bytes((root/'snapshot/board.kicad_pcb').read_bytes()+b'\n')
                else:data['source']=str(root/'other.kicad_pcb')
                with self.assertRaises((p.Rejected,ValueError,FileNotFoundError)):self.replay(root,data,base)


if __name__ == '__main__':
    unittest.main()
