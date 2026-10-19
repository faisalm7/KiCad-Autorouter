"""Constructed product readback/protection regressions, not Native qualification."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import config as c, default_targets as d, pipeline as p, sexpr as sx
from tests.test_default_targets import fixtures


class DefaultTargetIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.original_raw, self.native, self.project, self.original = fixtures()
        self.snapshot = self.root/'snapshot'/'owned.kicad_pcb'
        self.candidate = self.root/'candidate'/'owned.kicad_pcb'
        self.raw_task = (sx.dump(p.routing_task(self.original, 'whole_board_unlocked_routing'))+'\n').encode()
        for path in (self.snapshot, self.candidate):
            path.parent.mkdir(); path.write_bytes(self.raw_task)
            path.with_suffix('.kicad_pro').write_text(json.dumps(self.project))
        self.native.update(source=str(self.candidate), board_sha256=p.sha(self.candidate),
                           project_sha256=p.sha(self.candidate.with_suffix('.kicad_pro')))
        self.code = self.root/'code'/'pipeline.py'; self.code.parent.mkdir()
        self.code.write_bytes(Path(p.__file__).read_bytes())
        self.data = dict(source=str(self.snapshot), scope='whole_board_unlocked_routing', adapter='both',
                         source_hashes=p.tree_hash(self.snapshot.parent), task_sha256=p.sha(self.candidate),
                         tools={'implementation_sha256': {'autorouter/pipeline.py': p.sha(self.code)}})
        self.write('export-netclasses.json', self.native)
        (self.root/'native.dsn').write_bytes(self.original_raw)
        guided, self.record = d.transform(self.original_raw, self.native,
            self.candidate.with_suffix('.kicad_pro').read_bytes(), self.raw_task, source=str(self.candidate))
        (self.root/'default-targets.dsn').write_bytes(guided)
        self.write('default-targets.json', self.record)
        self.data['default_target_transport'] = dict(policy=d.POLICY, file='default-targets.json',
                                                    sha256=p.sha(self.root/'default-targets.json'))
        argv = [*p.native_prefix(), 'export', str(self.candidate), str(self.root/'task.dsn'),
                str(self.root/'export-netclasses.json'), '--task-copper-fixed']
        worker = dict(argv=argv, cwd=str(self.root), name='export', status='success', exit_code=0,
                      cleanup_complete=True)
        self.write('export-process.json', worker); self.data['steps'] = [worker]
        self.version = patch.object(c, 'NATIVE_VERSION', '10.0.7'); self.version.start()
        self.addCleanup(self.version.stop)

    def write(self, name, value):
        (self.root/name).write_text(json.dumps(value))

    def check(self):
        return p.check_default_target_transport(self.root, self.data, self.original, self.candidate)

    def test_actual_edit_rederived_from_snapshot_and_worker(self):
        self.assertEqual(self.check(), self.record)
        self.assertEqual(self.native['nets'][0]['width_nm'], 200000)
        self.assertEqual(self.record['derived_nm']['width_nm'], 300000)

    def test_deleting_all_markers_cannot_downgrade_current_producer(self):
        self.data.pop('default_target_transport')
        (self.root/'default-targets.json').unlink(); (self.root/'default-targets.dsn').unlink()
        with self.assertRaises((p.Rejected, FileNotFoundError)): self.check()

    def test_changed_proof_or_guidance_cannot_be_rehashed_into_authority(self):
        for kind in ('proof', 'guidance'):
            with self.subTest(kind=kind):
                if kind == 'proof':
                    wrong = copy.deepcopy(self.record); wrong['derived_nm']['width_nm'] = 200000
                    self.write('default-targets.json', wrong)
                    self.data['default_target_transport']['sha256'] = p.sha(self.root/'default-targets.json')
                else:
                    self.write('default-targets.json', self.record)
                    self.data['default_target_transport']['sha256'] = p.sha(self.root/'default-targets.json')
                    (self.root/'default-targets.dsn').write_bytes(self.original_raw)
                with self.assertRaises(p.Rejected): self.check()

    def test_raw_class_map_and_source_bindings_remain_mandatory(self):
        for key in ('project_sha256', 'board_sha256', 'source'):
            wrong = copy.deepcopy(self.native); wrong[key] = 'wrong'
            self.write('export-netclasses.json', wrong)
            with self.subTest(key=key), self.assertRaises(ValueError): self.check()
        wrong = copy.deepcopy(self.native); wrong['nets'][0]['width_nm'] = 300000
        self.write('export-netclasses.json', wrong)
        with self.assertRaises(ValueError): self.check()

    def test_real_worker_contract_cannot_omit_fixed_copper_or_mapping(self):
        for remove in ('--task-copper-fixed', str(self.root/'export-netclasses.json')):
            wrong = copy.deepcopy(self.data['steps'][0]); wrong['argv'].remove(remove)
            self.write('export-process.json', wrong); self.data['steps'] = [wrong]
            with self.subTest(remove=remove), self.assertRaises(p.Rejected): self.check()
            self.setUp_worker()

    def setUp_worker(self):
        worker = dict(argv=[*p.native_prefix(), 'export', str(self.candidate), str(self.root/'task.dsn'),
                           str(self.root/'export-netclasses.json'), '--task-copper-fixed'],
                      cwd=str(self.root), name='export', status='success', exit_code=0, cleanup_complete=True)
        self.write('export-process.json', worker); self.data['steps'] = [worker]

    def test_old_producer_is_historical_but_cannot_claim_new_guidance(self):
        self.code.write_text("NORMAL_ENGINE_PROVENANCE_POLICY='mandatory-normal-engine-journal-v1'\n")
        self.data['tools']['implementation_sha256']['autorouter/pipeline.py'] = p.sha(self.code)
        with self.assertRaises(p.Rejected): self.check()
        self.data.pop('default_target_transport')
        (self.root/'default-targets.json').unlink(); (self.root/'default-targets.dsn').unlink()
        self.assertIsNone(self.check())

    def test_stock_or_strategy_cannot_claim_direct_corrected_guidance(self):
        for key, value in [('adapter', 'none'), ('strategy', 'native_validated_thermal_bridge'),
                           ('scope', 'selected_nets')]:
            old = self.data.get(key); self.data[key] = value
            with self.subTest(key=key), self.assertRaises(p.Rejected): self.check()
            if old is None: self.data.pop(key)
            else: self.data[key] = old

    def final_evidence(self):
        self.write('final-netclasses.json', self.native)
        audited = p.audit_candidate_netclasses(self.candidate, [], self.native, default_target_policy=True)
        audited['native_map_file_sha256'] = p.sha(self.root/'final-netclasses.json')
        self.write('final-netclass-audit.json', audited)
        worker = dict(argv=[*p.native_prefix(), 'netclasses', str(self.candidate),
                           str(self.root/'final-netclasses.json')], cwd=str(self.root),
                      name='final-netclasses', status='success', exit_code=0, cleanup_complete=True)
        self.write('final-netclasses-process.json', worker)
        self.data['steps'] = [self.data['steps'][0], worker]

    def test_rejected_thermal_child_keeps_same_required_transport_and_final_audit(self):
        self.final_evidence()
        self.assertEqual(p.check_rejected_default_targets(self.root, self.data, self.original,
                                                        self.candidate, []), self.record)
        self.data.pop('default_target_transport')
        (self.root/'default-targets.json').unlink(); (self.root/'default-targets.dsn').unlink()
        with self.assertRaises((p.Rejected, FileNotFoundError)):
            p.check_rejected_default_targets(self.root, self.data, self.original, self.candidate, [])

    def test_rejected_child_cannot_rehash_wrong_derived_final_audit(self):
        self.final_evidence()
        audit = json.loads((self.root/'final-netclass-audit.json').read_text())
        audit['default_targets']['derived_nm']['width_nm'] = 200000
        self.write('final-netclass-audit.json', audit)
        with self.assertRaisesRegex(p.Rejected, 'netclass audit differs'):
            p.check_rejected_default_targets(self.root, self.data, self.original, self.candidate, [])

    def test_rejected_child_final_worker_cleanup_is_mandatory(self):
        self.final_evidence()
        worker = copy.deepcopy(self.data['steps'][-1]); worker['cleanup_complete'] = False
        self.write('final-netclasses-process.json', worker); self.data['steps'][-1] = worker
        with self.assertRaises(p.Rejected):
            p.check_rejected_default_targets(self.root, self.data, self.original, self.candidate, [])

    def test_genuine_older_rejected_child_never_gets_new_qualification(self):
        self.code.write_text("NORMAL_ENGINE_PROVENANCE_POLICY='mandatory-normal-engine-journal-v1'\n")
        self.data['tools']['implementation_sha256']['autorouter/pipeline.py'] = p.sha(self.code)
        self.data.pop('default_target_transport')
        (self.root/'default-targets.json').unlink(); (self.root/'default-targets.dsn').unlink()
        self.assertIsNone(p.check_rejected_default_targets(self.root, self.data, self.original,
                                                         self.candidate, []))

    def test_generated_geometry_uses_derived_targets_raw_class_stays_original(self):
        node = ['segment', ['start', '0', '0'], ['end', '1', '0'], ['width', '.3'],
                ['layer', '"F.Cu"'], ['net', '"DATA"']]
        board = copy.deepcopy(self.original); board.append(node); sx.write(self.candidate, board)
        native = copy.deepcopy(self.native); native['board_sha256'] = p.sha(self.candidate)
        audit = p.audit_candidate_netclasses(self.candidate, [], native, default_target_policy=True)
        self.assertEqual(audit['route_dimensions']['checked']['segments'], 1)
        self.assertEqual(audit['default_targets']['raw_nm']['width_nm'], 200000)
        self.assertEqual(audit['default_targets']['derived_nm']['width_nm'], 300000)
        self.assertEqual(native['nets'][0]['width_nm'], 200000)
        sx.one(node, 'width')[1] = '.2'; sx.write(self.candidate, board)
        native['board_sha256'] = p.sha(self.candidate)
        with self.assertRaisesRegex(p.Rejected, 'generated track differs'):
            p.audit_candidate_netclasses(self.candidate, [], native, default_target_policy=True)
        # Exact original protected geometry is exempt from target equality;
        # the normal immutable/protected/Native checks remain separate.
        audit = p.audit_candidate_netclasses(self.candidate, [node], native, default_target_policy=True)
        self.assertEqual(audit['route_dimensions']['checked']['protected'], 1)


if __name__ == '__main__': unittest.main()
