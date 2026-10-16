"""Constructed worker journals test evidence plumbing, never Native correctness.

SPDX-License-Identifier: GPL-3.0-or-later

No CLI/Python Native worker or routing engine runs here. The owned copied-file
PRL lifecycle is real where the host supports it; packet/netlist/worker records
are deliberately constructed. Actual Native qualification is a separate gate.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from autorouter import config as c, handoff as h, pipeline as p, placement_clearance as pc
from autorouter import schematic_class_evidence as e, schematic_classes as q, sexpr as sx
from tests import test_flat_class_parity as prior


def encoded(tree):
    return (sx.dump(tree) + '\n').encode()


def raw_json(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class _ConstructedJob:
    """Writes known synthetic process records; does not execute argv."""
    protect_local_settings = True

    def __init__(self, folder, netlist):
        self.out = folder; self.steps = []; self.netlist = copy.deepcopy(netlist)
        self._local_settings_owner = {}; h.capture_destination(self._local_settings_owner, folder)
        self.callback = None

    def journal(self, name, argv):
        log = self.out/(name+'.log'); log.write_bytes(b'constructed test worker; not Native\n')
        process = {'name': name, 'cwd': str(self.out), 'argv': argv, 'status': 'success',
            'exit_code': 0, 'cleanup_complete': True, 'log': str(log),
            'log_bytes': log.stat().st_size, 'log_truncated': False,
            'wall_seconds': .001, 'cpu_seconds': 0., 'monitor_cpu_seconds': 0.}
        self.steps.append(process); (self.out/(name+'-process.json')).write_bytes(raw_json(process))
        return process

    def step(self, name, argv):
        tree = copy.deepcopy(self.netlist)
        sx.one(sx.one(tree, 'design'), 'source')[1] = json.dumps(argv[-1])
        Path(argv[-2]).write_bytes(encoded(tree))
        result = self.journal(name, argv)
        if self.callback: self.callback(self, name, argv)
        return result


@unittest.skipUnless(hasattr(os, 'chflags') and hasattr(stat, 'UF_IMMUTABLE'),
                     'actual owned PRL guard requires its declared Mac host')
class SchematicClassEvidenceControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.fixture = prior.FlatClassParityControls(); self.fixture.setUp()
        self.count = 0

    def case(self, stage='task'):
        self.count += 1; root = self.root/str(self.count); root.mkdir(); candidate = root/'candidate'; candidate.mkdir()
        board = candidate/Path(self.fixture.source).name
        board.write_bytes(self.fixture.board_raw)
        board.with_suffix('.kicad_pro').write_bytes(self.fixture.project_raw)
        board.with_suffix('.kicad_sch').write_bytes(encoded(self.fixture.sch))
        board.with_suffix('.kicad_prl').write_bytes(b'{"owned_test_settings":true}\n')
        job = _ConstructedJob(root, self.fixture.netlist)
        native = copy.deepcopy(self.fixture.native); native['source'] = str(board)
        map_path = root/('export-netclasses.json' if stage == 'task' else 'final-netclasses.json')
        map_path.write_bytes(raw_json(native))
        name = 'export' if stage == 'task' else 'final-netclasses'
        argv = [str(c.PYTHON), str(c.ROOT/'autorouter/native.py'),
                'export' if stage == 'task' else 'netclasses', str(board),
                str(root/'task.dsn') if stage == 'task' else str(map_path)]
        if stage == 'task': argv.append(str(map_path))
        job.journal(name, argv)
        return {'job': job, 'board': board, 'map': map_path, 'stage': stage,
            'raw': {'board_raw': pc.read_bytes(board), 'project_raw': pc.read_bytes(board.with_suffix('.kicad_pro')),
                    'schematic_raw': pc.read_bytes(board.with_suffix('.kicad_sch'))},
            'source_hashes': pc.inventory(candidate)}

    def collect(self, case):
        metadata = e.collect(case['job'], case['stage'], case['board'], case['map'])
        case['data'] = {'steps': case['job'].steps, 'source_hashes': case['source_hashes'],
                        e.record_key(case['stage']): metadata}
        return metadata

    def check(self, case, *, data=None, **overrides):
        arguments = {**case['raw'], 'source': str(case['board']), 'native_map': case['map']}
        arguments.update(overrides)
        return e.check(case['job'].out, case['data'] if data is None else data, case['stage'], **arguments)

    def refused(self, case, **kwargs):
        with self.assertRaises((ValueError, p.Rejected)) as caught: self.check(case, **kwargs)
        return caught.exception

    def test_task_and_final_collect_and_replay_all_partitions_without_routing_admission(self):
        for stage in e.STAGES:
            with self.subTest(stage=stage):
                case = self.case(stage); metadata = self.collect(case); proof = self.check(case)
                self.assertEqual(metadata['context'], e.CONTEXT)
                self.assertEqual(metadata['file'], stage+'-classes-proof.json')
                self.assertEqual(proof['qualification']['nets'], 3)
                self.assertEqual(proof['qualification']['terminals'], 6)
                for name in ('accepted', 'routing_accepted', 'production_qualified'):
                    self.assertIs(proof['qualification'][name], False)
                self.assertEqual(pc.inventory(case['board'].parent), case['source_hashes'])
                process = e._json(case['job'].out/(e.step_name(stage)+'-process.json'))
                self.assertNotIn('local_settings_policy', process)
                binding = e._json(e.paths(case['job'].out, stage)['binding'])
                self.assertIs(binding['protection']['flags_restored'], True)
                self.assertIs(binding['protection']['bytes_unchanged'], True)

    def test_requirement_is_pending_only_and_unchanged_no_flag_returns_none(self):
        case = self.case(); before = pc.inventory(case['board'].parent)
        pending = e.requirement(case['board'])
        self.assertEqual(pending['status'], 'pending_native_class_parity')
        self.assertIs(pending['native_validation_performed'], False)
        self.assertIs(pending['class_parity_qualified'], False)
        self.assertEqual(pending['source_hashes'], before)
        sch = copy.deepcopy(self.fixture.sch); sch.remove(sx.one(sch, 'netclass_flag'))
        case['board'].with_suffix('.kicad_sch').write_bytes(encoded(sch))
        self.assertIsNone(e.requirement(case['board']))

    def test_requirement_refuses_hierarchy_hidden_flag_and_unqualified_source(self):
        for kind in ('hierarchy', 'hidden_flag', 'bad_class', 'missing_board'):
            with self.subTest(kind=kind):
                case = self.case(); sch = copy.deepcopy(self.fixture.sch)
                if kind == 'hierarchy': sch.append(['sheet', ['property', '"Sheetfile"', '"child.kicad_sch"']])
                elif kind == 'hidden_flag': (case['board'].parent/'unpaired.kicad_sch').write_bytes(encoded(sch))
                elif kind == 'bad_class': sx.one(sx.one(sch, 'netclass_flag'), 'property')[2] = '"Unknown"'
                else: case['board'].unlink()
                case['board'].with_suffix('.kicad_sch').write_bytes(encoded(sch))
                with self.assertRaises((ValueError, p.Rejected)): e.requirement(case['board'])

    def test_missing_downgraded_boolean_and_extra_proof_metadata_refuse(self):
        case = self.case(); self.collect(case)
        for kind in ('missing', 'context', 'schema_bool', 'stage', 'sha', 'extra'):
            with self.subTest(kind=kind):
                data = copy.deepcopy(case['data']); metadata = data[e.record_key('task')]
                if kind == 'missing': del data[e.record_key('task')]
                elif kind == 'context': metadata['context'] = 'legacy'
                elif kind == 'schema_bool': metadata['schema'] = True
                elif kind == 'stage': metadata['stage'] = 'final'
                elif kind == 'sha': metadata['sha256'] = '0'*64
                else: metadata['unknown'] = True
                self.refused(case, data=data)

    def test_map_input_binding_proof_and_process_json_whitespace_changes_refuse(self):
        for kind in ('map', 'input', 'binding', 'proof', 'process'):
            with self.subTest(kind=kind):
                case = self.case(); self.collect(case); files = e.paths(case['job'].out, 'task')
                path = {'map': case['map'], 'input': files['input']/case['board'].name,
                        'binding': files['binding'], 'proof': files['proof'],
                        'process': case['job'].out/'task-classes-netlist-process.json'}[kind]
                path.write_bytes(path.read_bytes()+b'\n')
                self.refused(case)

    def test_class_netlist_and_map_worker_logs_cannot_change_or_truncate(self):
        for name in ('task-classes-netlist', 'export'):
            for kind in ('log', 'truncated', 'missing_step', 'argv'):
                with self.subTest(name=name, kind=kind):
                    case = self.case(); self.collect(case); folder = case['job'].out
                    if kind == 'log': (folder/(name+'.log')).write_bytes(b'changed')
                    elif kind == 'missing_step':
                        case['data']['steps'] = [x for x in case['data']['steps'] if x['name'] != name]
                    else:
                        path = folder/(name+'-process.json'); record = json.loads(path.read_bytes())
                        if kind == 'truncated': record['log_truncated'] = True
                        else: record['argv'][-1] = '/unrelated/project.kicad_sch'
                        path.write_bytes(raw_json(record))
                        for index, step in enumerate(case['data']['steps']):
                            if step['name'] == name: case['data']['steps'][index] = record
                    self.refused(case)

    def test_copied_and_live_companion_prl_and_passed_source_binding_refuse(self):
        for kind in ('copy_prl', 'copy_sch', 'live_pro', 'live_sch', 'passed_pro',
                     'missing_source_board', 'wrong_source', 'wrong_map_path'):
            with self.subTest(kind=kind):
                case = self.case(); self.collect(case); files = e.paths(case['job'].out, 'task'); kwargs = {}
                if kind == 'copy_prl':
                    path = (files['input']/case['board'].name).with_suffix('.kicad_prl'); path.write_bytes(b'{}\n')
                elif kind == 'copy_sch':
                    path = (files['input']/case['board'].name).with_suffix('.kicad_sch'); path.write_bytes(path.read_bytes()+b'\n')
                elif kind in ('live_pro', 'live_sch'):
                    path = case['board'].with_suffix('.kicad_pro' if kind == 'live_pro' else '.kicad_sch')
                    path.write_bytes(path.read_bytes()+b'\n')
                elif kind == 'passed_pro': kwargs['project_raw'] = case['raw']['project_raw']+b'\n'
                elif kind == 'missing_source_board': del case['data']['source_hashes'][case['board'].name]
                elif kind == 'wrong_source': kwargs['source'] = str(case['board']).replace('/candidate/', '/other/')
                else: kwargs['native_map'] = case['job'].out/'other.json'
                self.refused(case, **kwargs)

    def test_task_replay_uses_reconstructed_bytes_and_never_reads_current_pcb(self):
        case = self.case(); self.collect(case)
        case['board'].write_bytes(b'this later candidate PCB must not be read by task replay')
        proof = self.check(case)
        self.assertEqual(proof['qualification']['sha256']['board'], sha(case['raw']['board_raw']))

    def test_late_map_and_proof_mutations_refuse(self):
        case = self.case(); self.collect(case); real = e.q.derive
        def mutate_map(*args, **kwargs):
            result = real(*args, **kwargs)
            case['map'].write_bytes(case['map'].read_bytes()+b'\n')
            return result
        with patch.object(e.q, 'derive', side_effect=mutate_map): self.refused(case)
        case = self.case(); self.collect(case); real_rederive = e._rederive
        def mutate_proof(*args, **kwargs):
            result = real_rederive(*args, **kwargs); path = e.paths(case['job'].out, 'task')['proof']
            path.write_bytes(path.read_bytes()+b'\n'); return result
        with patch.object(e, '_rederive', side_effect=mutate_proof): self.refused(case)

    def test_guard_event_cannot_be_removed_or_claimed_not_present_with_rehashed_binding(self):
        for kind in ('removed', 'false_presence'):
            with self.subTest(kind=kind):
                case = self.case(); self.collect(case); files = e.paths(case['job'].out, 'task')
                binding = json.loads(files['binding'].read_bytes())
                if kind == 'removed': binding['protection'] = None
                else: binding['protection'] = {'policy': e.local.POLICY, 'present': False}
                files['binding'].write_bytes(raw_json(binding))
                # Updating the outer hash cannot manufacture the actual guard.
                proof = json.loads(files['proof'].read_bytes()); proof['binding_sha256'] = sha(files['binding'].read_bytes())
                files['proof'].write_bytes(raw_json(proof)); case['data'][e.record_key('task')]['sha256'] = sha(files['proof'].read_bytes())
                self.refused(case)

    def test_rehashed_positive_proof_cannot_claim_acceptance_or_boolean_schema(self):
        for kind in ('accepted', 'boolean_schema'):
            with self.subTest(kind=kind):
                case = self.case(); self.collect(case); path = e.paths(case['job'].out, 'task')['proof']
                proof = json.loads(path.read_bytes())
                if kind == 'accepted': proof['qualification']['accepted'] = True
                else: proof['schema'] = True
                path.write_bytes(raw_json(proof)); case['data'][e.record_key('task')]['sha256'] = sha(path.read_bytes())
                self.refused(case)

    def test_late_prl_flags_are_rechecked_after_pure_comparison(self):
        case = self.case(); self.collect(case); real = e.q.derive
        prl = (e.paths(case['job'].out, 'task')['input']/case['board'].name).with_suffix('.kicad_prl')
        def mutate_flags(*args, **kwargs):
            result = real(*args, **kwargs)
            os.chflags(prl, stat.UF_IMMUTABLE, follow_symlinks=False)
            return result
        try:
            with patch.object(e.q, 'derive', side_effect=mutate_flags): self.refused(case)
        finally:
            os.chflags(prl, 0, follow_symlinks=False)

    def test_collect_refuses_changed_map_before_worker_and_repeated_paths(self):
        case = self.case(); native = json.loads(case['map'].read_bytes()); native['board_sha256'] = '0'*64
        case['map'].write_bytes(raw_json(native))
        with self.assertRaises((ValueError, p.Rejected)): self.collect(case)
        self.assertEqual(len(case['job'].steps), 1)
        case = self.case(); self.collect(case)
        with self.assertRaises((ValueError, p.Rejected)): self.collect(case)
        self.assertEqual(len(case['job'].steps), 2)

    def test_collect_detects_source_change_during_worker_and_restores_guard(self):
        case = self.case()
        def mutate(job, name, argv): case['board'].with_suffix('.kicad_sch').write_bytes(b'changed')
        case['job'].callback = mutate
        with self.assertRaises((ValueError, p.Rejected)): self.collect(case)
        prl = (e.paths(case['job'].out, 'task')['input']/case['board'].name).with_suffix('.kicad_prl')
        self.assertEqual(prl.stat().st_flags, 0)
        self.assertFalse(e.paths(case['job'].out, 'task')['proof'].exists())

    def test_malformed_payload_unknown_stage_and_missing_proof_refuse(self):
        case = self.case(); self.collect(case)
        for stage in ('source', '', True):
            with self.subTest(stage=stage), self.assertRaises(ValueError): e.paths(case['job'].out, stage)
        for key in ('board_raw', 'project_raw', 'schematic_raw'):
            with self.subTest(key=key): self.refused(case, **{key: b'corrupt'})
        files = e.paths(case['job'].out, 'task'); files['proof'].unlink()
        with self.assertRaises((ValueError, p.Rejected, OSError)): self.check(case)


if __name__ == '__main__':
    unittest.main()
