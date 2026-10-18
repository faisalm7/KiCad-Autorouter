"""Authored thermal-parent admission controls, never Native evidence.

Reuse the synthetic saved-import/refill builder and named DSN transform inputs.
Only the unrelated final thermal report binding is mocked. The real import
census, recursive import contract, captured policy and named edge replay run.
"""
import copy
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from autorouter import adapter, floor_route as f, native_edge, pipeline as p
from autorouter import placement_clearance as pc, sexpr as sx, thermal
from tests import test_native_edge as edge_fixture
from tests import test_native_edge_named as named_fixture
from tests import test_normal_selected_import as import_fixture


class RejectedThermalIncumbentNamedEdge(unittest.TestCase):
    make = import_fixture.NormalSelectedImportControls.make

    def parent_fixture(self):
        root, child, original, candidate, _ = self.make(
            protected=True, nested=True, selected=False)
        work = root / 'incumbent'
        source = Path(child['source'])
        tree, _, project = named_fixture.inputs()
        tree.append(['placement'])
        rectangle = sx.one(sx.parse(edge_fixture.BOARD.decode()), 'gr_rect')
        sx.one(rectangle, 'uuid')[1] = '"50ad65ef-c652-5f95-9f39-3f46a9b9f347"'
        original.append(copy.deepcopy(rectangle))
        p.routes(original)[0].append(['locked', 'yes'])
        sx.write(source, original)
        imported = sx.read(work / 'imported.kicad_pcb')
        imported.append(copy.deepcopy(rectangle))
        p.routes(imported)[0][:] = copy.deepcopy(p.routes(original)[0])
        protected = [route for route in p.routes(original) if p.locked(route)]
        proof = {}
        emitted = p.transplant_routes(
            original, imported, protected=protected, audit=proof,
            policy='exact_non_uuid_lock_position_v2')
        self.assertEqual(len(protected), 1)
        self.assertEqual(len(proof['matches']), 1)
        for path in (candidate, work / 'refill' / source.name):
            sx.write(path, emitted)
        sx.write(work / 'imported.kicad_pcb', imported)
        project_raw = json.dumps(project).encode()
        for board in (source, candidate, work / 'refill' / source.name):
            board.with_suffix('.kicad_pro').write_bytes(project_raw)
        (work / 'pre-refill.kicad_pcb').write_bytes(candidate.read_bytes())
        child['source_hashes'] = p.tree_hash(source.parent)
        child['candidate_sha256'] = p.sha(candidate)
        child['protected_route_import'] = {
            'imported_sha256': p.sha(work / 'imported.kicad_pcb'), **proof}
        transport = work / 'imported.routes-only.json'
        metadata = f.read_json(transport)
        metadata['imported_board_sha256'] = p.sha(work / 'imported.kicad_pcb')
        p.save_json(transport, metadata)
        refill_binding = work / 'refill-drc-binding.json'
        binding = f.read_json(refill_binding)
        binding['before'] = binding['after'] = p.tree_hash(work / 'refill')
        p.save_json(refill_binding, binding)
        next(step for step in child['steps'] if step['name'] == 'refill-drc')[
            'validated_input_sha256'] = p.sha(work / 'refill' / source.name)

        # Captured bytes are inspected as data; no captured code is executed.
        # This fixture replaces the minimal historical producer with current
        # code, so author its current declaration before any deliberate faults.
        child['tools']['normal_protected_via_import_policy']=p.NORMAL_PROTECTED_VIA_IMPORT_POLICY
        code = root / 'code'
        package = Path(p.__file__).resolve().parent
        for name in ('pipeline.py', 'recovery.py', 'native_edge.py'):
            (code / name).write_bytes((package / name).read_bytes())
        child['tools']['implementation_sha256'] = {
            'autorouter/' + path.name: p.sha(path) for path in code.iterdir()}
        shutil.copytree(code, work / 'code')
        shutil.copytree(source.parent, work / 'snapshot')
        snapshot = work / 'snapshot' / source.name
        raw = adapter._dump_dsn(tree).encode()
        adapted, transform = adapter.adapt_bytes(raw, 'both', [])
        corrected, edge = native_edge.correct(
            adapted, p.native_edge_context(snapshot, known_named=True))
        self.assertTrue(edge['applied'])
        self.assertIn('named_class_scope', edge)
        (work / 'native.dsn').write_bytes(raw)
        (work / 'edge-adapter-input.dsn').write_bytes(adapted)
        (work / 'task.dsn').write_bytes(corrected)
        p.save_json(work / 'obstacles.json', [])
        p.save_json(work / 'native-edge-correction.json', edge)
        child.update(
            adapter='both', engine_profile='completion-only',
            accepted=False, status='drc_rejected',
            native_edge_admission_policy=p.NAMED_EDGE_ADMISSION_POLICY,
            native_edge_correction=edge, adapter_transformations=transform,
            native=dict(opens=0, blocking=1, warnings=0, exclusions=0,
                        ignored_checks=[], findings=[dict(
                            type='starved_thermal', severity='error',
                            items=[{'uuid': 'authored-zone'}, {'uuid': 'authored-pad'}])]))
        self.assertIsNotNone(thermal.sole_thermal(child['native']))
        parent = dict(
            schema=1, baseline='C-prototype',
            strategy='native_validated_thermal_bridge', adapter='both',
            scope='whole_board_unlocked_routing', source=child['source'],
            source_hashes=copy.deepcopy(child['source_hashes']),
            tools=copy.deepcopy(child['tools']),
            steps=[dict(step, phase='incumbent') for step in child['steps']])

        def sync_child():
            p.save_json(work / 'result.json', child)
            parent['incumbent'] = dict(
                receipt=str(work / 'result.json'),
                receipt_sha256=p.sha(work / 'result.json'),
                status=child['status'], accepted=child['accepted'])

        def check():
            sync_child()
            retained = pc.inventory(root, max_bytes=4 * 1024**2,
                                    max_files=150, max_entries=300)
            imports = adapter.check_fixed_placement_import(root, parent, retained)
            self.assertEqual(imports, [dict(
                cwd=str(work), name='import', source=str(candidate),
                output=str(work / 'imported.kicad_pcb'),
                session=str(work / 'routes.ses'))])
            return p.normal_import_contract(
                root, parent, imports, input_policy='native', original=original)

        return root, work, parent, child, check

    def test_sole_thermal_parent_replays_actual_child_admission_and_named_edge(self):
        root, work, parent, child, check = self.parent_fixture()
        self.assertNotIn('native_edge_admission_policy', parent)
        before = pc.inventory(root)
        with patch.object(thermal, '_report_binding') as report_binding, \
                patch.object(p, 'check_named_edge_policy', wraps=p.check_named_edge_policy) as policy, \
                patch.object(p, 'check_native_edge_transport', wraps=p.check_native_edge_transport) as edge, \
                patch.object(p, 'check_result', side_effect=AssertionError('rejected child is not accepted')):
            self.assertIsNone(check())
        report_binding.assert_called_once()
        policy.assert_called_once()
        self.assertEqual(policy.call_args.args[0], work)
        self.assertTrue(policy.call_args.kwargs['direct_import'])
        edge.assert_called_once()
        self.assertEqual(edge.call_args.args[0], work)
        self.assertIs(edge.call_args.kwargs['_known_named_edge'], True)
        # Only publication of the explicitly authored child receipt is new.
        after = pc.inventory(root)
        self.assertEqual({k: v for k, v in after.items() if k != 'incumbent/result.json'}, before)
        self.assertFalse(child['accepted'])

    def test_deleted_or_foreign_child_marker_cannot_hide_behind_parent_hash_update(self):
        _, work, _, child, check = self.parent_fixture()
        for marker in (None, 'unqualified-foreign-policy'):
            with self.subTest(marker=marker):
                if marker is None:
                    child.pop('native_edge_admission_policy', None)
                else:
                    child['native_edge_admission_policy'] = marker
                with patch.object(thermal, '_report_binding') as report_binding:
                    with self.assertRaisesRegex(p.Rejected, 'named edge admission policy'):
                        check()  # Refreshes the parent's exact child-receipt hash.
                report_binding.assert_called_once()
                self.assertTrue((work / 'native-edge-correction.json').is_file())

    def test_intact_marker_still_requires_child_edge_engine_input(self):
        _, work, _, _, check = self.parent_fixture()
        (work / 'task.dsn').write_bytes((work / 'native.dsn').read_bytes())
        with patch.object(thermal, '_report_binding') as report_binding:
            with self.assertRaisesRegex(p.Rejected, 'native edge correction input'):
                check()
        report_binding.assert_called_once()


if __name__ == '__main__':
    unittest.main()
