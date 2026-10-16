"""Prospective diagnostic binding controls, never Native/net-tie admission."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from autorouter import pipeline as p, floor_route as f
from experiments.net_tie_contact_v1 import driver


class ContactProcessBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve(); self.out=self.root/'job'; self.out.mkdir()
        self.command=['owned-native','owned-worker','owned-input','owned-dsn','owned-json']
        self.log=self.out/'contact-observation.log'; self.log.write_bytes(b'observed\n')
        self.process=dict(argv=[*f.SANDBOX,*self.command],cwd=str(self.out),name='contact-observation',
            exit_code=0,status='success',cleanup_complete=True,log_truncated=False,log_bytes=9)
        self.journal=self.out/'contact-observation-process.json'
        self.journal.write_text(json.dumps(self.process))
        self.job=SimpleNamespace(out=self.out,steps=[dict(self.process)])
        self.dsn=self.root/'observed.dsn'; self.dsn.write_bytes(b'original')
        self.proof=self.root/'observation.json'
        self.proof.write_text(json.dumps(dict(export={'dsn_sha256':p.sha(self.dsn)},
            dsn_membership={'dsn_sha256':p.sha(self.dsn)})))
        self.expected=(p.sha(self.log),p.sha(self.proof),p.sha(self.dsn))

    def replay(self):
        driver.replay_observation(self.job,self.command,self.process,self.expected[0],
            self.root,self.expected[1],self.expected[2])

    def test_actual_shared_process_and_bound_files_replay(self):
        self.replay()
        changed=json.loads(self.journal.read_text()); changed['argv']=['different']; self.journal.write_text(json.dumps(changed))
        with self.assertRaises(p.Rejected): self.replay()

    def test_same_size_DSN_replacement_before_initial_snapshot_refuses(self):
        self.dsn.write_bytes(b'replaced')
        # Model the original bug: freeze the replacement hash after worker exit.
        self.expected=(self.expected[0],self.expected[1],p.sha(self.dsn))
        with self.assertRaisesRegex(p.Rejected,'worker export/membership'): self.replay()

    def test_deleted_or_same_size_changed_log_refuses(self):
        self.log.write_bytes(b'changed!\n')
        with self.assertRaises(p.Rejected): self.replay()
        self.log.unlink()
        with self.assertRaises((OSError,p.Rejected)): self.replay()

    def test_one_embedded_DSN_binding_cannot_substitute_for_both(self):
        proof=json.loads(self.proof.read_text()); proof['dsn_membership']['dsn_sha256']='0'*64
        self.proof.write_text(json.dumps(proof))
        self.expected=(self.expected[0],p.sha(self.proof),self.expected[2])
        with self.assertRaisesRegex(p.Rejected,'worker export/membership'): self.replay()

    def test_shared_publication_late_invalidation_clears_case_passes(self):
        result=dict(accepted=False,passed=True,status='completed',
                    cases={'positive':dict(control_passed=True,native={'warnings':7})})
        calls=[]
        def stable():
            calls.append(True)
            if len(calls)>1: raise p.Rejected('injected late candidate change')
        f.publish(self.root,result,stable,lambda:driver.clear_unqualified_controls(result),lambda:30)
        stored=json.loads((self.root/'result.json').read_text())
        self.assertEqual(stored['status'],'invalidated')
        self.assertFalse(stored['passed']); self.assertFalse(stored['cases']['positive']['control_passed'])
        self.assertEqual(stored['cases']['positive']['native'],{'warnings':7})
        self.assertTrue(list(self.root.glob('invalidated-result-*.json')))
