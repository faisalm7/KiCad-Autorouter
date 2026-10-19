"""Constructed hierarchy worker evidence plus real owned Mac PRL guards.

SPDX-License-Identifier: GPL-3.0-or-later
The version patch selects comparator expectations only. No actual selected
Native tool, KiCad export, route, engine or Native correctness is established.
"""
import copy
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from autorouter import config as c, pipeline as p, placement_clearance as pc
from autorouter import schematic_class_evidence as e, sexpr as sx
from experiments import schematic_hierarchy_fixture as fixture
from tests import test_schematic_class_evidence as prior


@unittest.skipUnless(hasattr(os, 'chflags') and hasattr(stat, 'UF_IMMUTABLE'),
                     'real owned PRL protection requires the declared Mac host')
class HierarchyEvidenceControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.version = patch.object(c, 'NATIVE_VERSION', '10.0.7')
        self.version.start(); self.addCleanup(self.version.stop)
        self.count = 0

    def case(self, stage='task', *, prl=True):
        self.count += 1
        folder = self.root / str(self.count); folder.mkdir()
        candidate = folder / 'candidate'; candidate.mkdir()
        value = fixture.case()
        raw = fixture.arguments(value)
        board = candidate / (fixture.STEM + '.kicad_pcb')
        board.write_bytes(raw['board_raw'])
        board.with_suffix('.kicad_pro').write_bytes(raw['project_raw'])
        for name, data in raw['schematics'].items():
            (candidate / name).write_bytes(data)
        if prl:
            board.with_suffix('.kicad_prl').write_bytes(b'{"owned_settings":true}\n')
        job = prior._ConstructedJob(folder, value['netlist'])
        native = json.loads(raw['native_raw']); native['source'] = str(board)
        mapping = folder / ('export-netclasses.json' if stage == 'task' else 'final-netclasses.json')
        mapping.write_bytes(prior.raw_json(native))
        name = 'export' if stage == 'task' else 'final-netclasses'
        argv = [str(c.PYTHON), str(c.ROOT / 'autorouter/native.py'),
                'export' if stage == 'task' else 'netclasses', str(board),
                str(folder / 'task.dsn') if stage == 'task' else str(mapping)]
        if stage == 'task': argv.extend([str(mapping), '--task-copper-fixed'])
        job.journal(name, argv)
        return dict(job=job, board=board, map=mapping, stage=stage,
                    source_hashes=pc.inventory(candidate),
                    raw=dict(board_raw=raw['board_raw'], project_raw=raw['project_raw'],
                             schematic_raw=raw['schematics'][fixture.ROOT_SCH]))

    def collect(self, case):
        metadata = e.collect(case['job'], case['stage'], case['board'], case['map'])
        case['data'] = dict(steps=case['job'].steps, source_hashes=case['source_hashes'],
                            **{e.record_key(case['stage']): metadata})
        return metadata

    def check(self, case, *, data=None):
        return e.check(case['job'].out, case['data'] if data is None else data, case['stage'],
                       source=str(case['board']), native_map=case['map'], **case['raw'])

    def refused(self, case, *, data=None):
        with self.assertRaises((ValueError, p.Rejected, OSError)):
            self.check(case, data=data)

    def paths(self, case):
        return e.paths(case['job'].out, case['stage'])

    def rebind(self, case, *, binding=None, proof=None):
        """Reauthor outer hashes only; the shared reader must rederive meaning."""
        files = self.paths(case)
        if binding is not None:
            files['binding'].write_bytes(prior.raw_json(binding))
        proof = json.loads(files['proof'].read_bytes()) if proof is None else proof
        proof['binding_sha256'] = prior.sha(files['binding'].read_bytes())
        files['proof'].write_bytes(prior.raw_json(proof))
        case['data'][e.record_key(case['stage'])]['sha256'] = prior.sha(files['proof'].read_bytes())

    def test_requirement_is_source_bound_pending_only_and_version_specific(self):
        case = self.case(); before = pc.inventory(case['board'].parent)
        required = e.requirement(case['board'])
        self.assertEqual(required['context'], e.HIERARCHY_CONTEXT)
        self.assertEqual((required['components'], required['terminals'], required['instances']), (5, 11, 3))
        self.assertEqual(required['source_hashes'], before)
        for key in ('native_validation_performed', 'class_parity_qualified', 'accepted',
                    'routing_accepted', 'production_qualified'):
            self.assertIs(required[key], False)
        with patch.object(c, 'NATIVE_VERSION', '10.0.0'):
            with self.assertRaises(ValueError): e.requirement(case['board'])
        self.assertEqual(pc.inventory(case['board'].parent), before)

    def test_task_and_final_real_PRL_guard_collect_replay_and_full_closure(self):
        for stage in e.STAGES:
            with self.subTest(stage=stage):
                case = self.case(stage); observed = []
                def during_worker(job, name, argv):
                    observed.append(Path(argv[-1]).with_suffix('.kicad_prl').stat().st_flags)
                case['job'].callback = during_worker
                metadata = self.collect(case); proof = self.check(case)
                self.assertEqual(metadata['context'], e.HIERARCHY_CONTEXT)
                self.assertEqual(proof['qualification']['instances'], 3)
                self.assertEqual(proof['qualification']['terminals'], 11)
                self.assertIs(proof['qualification']['accepted'], False)
                self.assertEqual(observed, [stat.UF_IMMUTABLE])
                files = self.paths(case); binding = json.loads(files['binding'].read_bytes())
                self.assertEqual(binding['before'], binding['after'])
                self.assertIs(binding['protection']['flags_restored'], True)
                self.assertIs(binding['protection']['bytes_unchanged'], True)
                self.assertEqual(binding['before'][fixture.CHILD_SCH],
                                 proof['qualification']['sha256']['schematics'][fixture.CHILD_SCH])
                self.assertEqual(pc.inventory(case['board'].parent), case['source_hashes'])

    def test_named_created_PRL_is_retained_and_bound_without_mutating_source(self):
        for stage in e.STAGES:
            with self.subTest(stage=stage):
                case = self.case(stage, prl=False)
                created = b'{"created_by_constructed_worker":true}\n'
                def create_prl(job, name, argv): Path(argv[-1]).with_suffix('.kicad_prl').write_bytes(created)
                case['job'].callback = create_prl
                self.collect(case); self.check(case)
                files = self.paths(case); binding = json.loads(files['binding'].read_bytes())
                prl_name = case['board'].with_suffix('.kicad_prl').name
                self.assertEqual(set(binding['after']) - set(binding['before']), {prl_name})
                self.assertEqual(binding['after'][prl_name], prior.sha(created))
                self.assertEqual(binding['protection'], {'policy': e.local.POLICY, 'present': False})
                self.assertFalse(case['board'].with_suffix('.kicad_prl').exists())
                self.assertEqual(pc.inventory(case['board'].parent), case['source_hashes'])

    def test_other_created_file_and_child_source_mutations_refuse_after_worker(self):
        for fault in ('new_file', 'copied_child', 'live_child'):
            with self.subTest(fault=fault):
                case = self.case(prl=False)
                def mutate(job, name, argv):
                    folder = Path(argv[-1]).parent
                    if fault == 'new_file': (folder / 'unexpected.txt').write_bytes(b'not permitted\n')
                    else:
                        path = (case['board'].parent if fault == 'live_child' else folder) / fixture.CHILD_SCH
                        path.write_bytes(path.read_bytes() + b'\n')
                case['job'].callback = mutate
                with self.assertRaises((ValueError, p.Rejected)): self.collect(case)
                self.assertFalse(self.paths(case)['proof'].exists())

    def test_existing_PRL_write_is_actually_blocked_and_guard_restored(self):
        case = self.case(); before = case['board'].with_suffix('.kicad_prl').read_bytes()
        def mutate(job, name, argv): Path(argv[-1]).with_suffix('.kicad_prl').write_bytes(b'changed')
        case['job'].callback = mutate
        with self.assertRaises(OSError): self.collect(case)
        copied = (self.paths(case)['input'] / case['board'].name).with_suffix('.kicad_prl')
        self.assertEqual(copied.read_bytes(), before)
        self.assertEqual(copied.stat().st_flags, 0)
        self.assertFalse(self.paths(case)['proof'].exists())

    def test_canceled_nonzero_and_unclean_constructed_workers_never_publish_proof(self):
        for fault in ('cancelled', 'nonzero', 'cleanup'):
            with self.subTest(fault=fault):
                case = self.case(prl=fault != 'cleanup')
                def alter_worker(job, name, argv):
                    row = job.steps[-1]
                    if fault == 'cancelled': row.update(status='cancelled', exit_code=-15)
                    elif fault == 'nonzero': row.update(status='nonzero_exit', exit_code=5)
                    else: row['cleanup_complete'] = False
                    (job.out / (name + '-process.json')).write_bytes(prior.raw_json(row))
                case['job'].callback = alter_worker
                with self.assertRaises((ValueError, p.Rejected)): self.collect(case)
                self.assertFalse(self.paths(case)['proof'].exists())

    def test_missing_or_wrong_map_refuses_before_schematic_worker(self):
        for fault in ('missing', 'wrong_hash'):
            with self.subTest(fault=fault):
                case = self.case()
                if fault == 'missing': case['map'].unlink()
                else:
                    native = json.loads(case['map'].read_bytes()); native['board_sha256'] = '0' * 64
                    case['map'].write_bytes(prior.raw_json(native))
                with self.assertRaises((ValueError, p.Rejected, OSError)): self.collect(case)
                self.assertEqual(len(case['job'].steps), 1)
                self.assertFalse(self.paths(case)['proof'].exists())

    def test_source_hierarchy_cannot_downgrade_to_flat_or_drop_policy(self):
        for fault in ('flat', 'policy', 'combined', 'metadata', 'old_context', 'old_policy', 'old_both'):
            with self.subTest(fault=fault):
                case = self.case(); self.collect(case)
                files = self.paths(case)
                binding, proof = (json.loads(files[key].read_bytes()) for key in ('binding', 'proof'))
                if fault in ('flat', 'combined'):
                    binding['context'] = proof['context'] = e.CONTEXT
                    case['data'][e.record_key('task')]['context'] = e.CONTEXT
                if fault in ('policy', 'combined'): del proof['qualification']['policy']
                if fault in ('old_context', 'old_both'):
                    binding['context'] = proof['context'] = 'native-route-hierarchy-default-v1'
                    case['data'][e.record_key('task')]['context'] = binding['context']
                if fault in ('old_policy', 'old_both'):
                    proof['qualification']['policy'] = 'hierarchy-default-instance-unit-v1'
                self.rebind(case, binding=binding, proof=proof)
                if fault == 'metadata': del case['data'][e.record_key('task')]
                self.refused(case)

    def test_semantic_stamp_fault_refuses_after_outer_receipt_hashes_are_reauthored(self):
        case = self.case(); self.collect(case); files = self.paths(case)
        netlist = sx.parse(files['netlist'].read_text())
        component = next(row for row in sx.children(sx.one(netlist, 'components'), 'comp')
                         if sx.one(row, 'ref')[1] == '"U1"')
        stamps = sx.one(component, 'tstamps'); stamps[1:] = list(reversed(stamps[1:]))
        files['netlist'].write_bytes(fixture.encoded(netlist))
        binding = json.loads(files['binding'].read_bytes())
        binding['netlist_sha256'] = prior.sha(files['netlist'].read_bytes())
        self.rebind(case, binding=binding)
        self.refused(case)

    def test_original_PRL_and_closure_mutations_cannot_be_accepted_by_rebinding_after(self):
        for fault in ('prl', 'child', 'created_extra'):
            with self.subTest(fault=fault):
                case = self.case(); self.collect(case); files = self.paths(case)
                if fault == 'prl':
                    path = (files['input'] / case['board'].name).with_suffix('.kicad_prl')
                elif fault == 'child': path = files['input'] / fixture.CHILD_SCH
                else: path = files['input'] / 'extra.kicad_pro'
                path.write_bytes(path.read_bytes() + b'\n' if path.exists() else b'{}\n')
                binding = json.loads(files['binding'].read_bytes())
                binding['after'] = pc.inventory(files['input'])
                self.rebind(case, binding=binding)
                self.refused(case)

    def test_actual_PRL_flags_are_replayed_after_hierarchy_derivation(self):
        case = self.case(); self.collect(case)
        prl = (self.paths(case)['input'] / case['board'].name).with_suffix('.kicad_prl')
        actual = e.hierarchy.derive
        def mutate_flags(*args, **kwargs):
            result = actual(*args, **kwargs)
            os.chflags(prl, stat.UF_IMMUTABLE, follow_symlinks=False)
            return result
        try:
            with patch.object(e.hierarchy, 'derive', side_effect=mutate_flags): self.refused(case)
        finally:
            os.chflags(prl, 0, follow_symlinks=False)

    def test_forged_closure_name_refuses_before_any_traversal_read(self):
        case = self.case(); self.collect(case)
        data = copy.deepcopy(case['data'])
        data['source_hashes']['../outside.kicad_sch'] = '0' * 64
        actual = pc.read_bytes; opened = []
        def observe(path, *args, **kwargs):
            opened.append(Path(path))
            return actual(path, *args, **kwargs)
        with patch.object(pc, 'read_bytes', side_effect=observe):
            self.refused(case, data=data)
        self.assertTrue(opened)
        self.assertFalse(any('..' in path.parts for path in opened))

    def test_unchanged_flat_context_collect_and_check_remain_compatible(self):
        # Comparator expectation0 only, with the existing owned flat fixture;
        # no selected Native tool or actual process is being changed here.
        with patch.object(c, 'NATIVE_VERSION', '10.0.0'):
            flat = prior.SchematicClassEvidenceControls()
            flat.setUp()
            try:
                case = flat.case(); metadata = flat.collect(case); proof = flat.check(case)
                self.assertEqual(metadata['context'], e.CONTEXT)
                self.assertEqual(proof['qualification']['policy'], e.q.POLICY)
                self.assertIs(proof['qualification']['accepted'], False)
            finally:
                flat.doCleanups()


if __name__ == '__main__':
    unittest.main()
