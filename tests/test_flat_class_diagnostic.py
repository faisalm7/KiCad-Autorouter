"""Retained proof provenance and specific diagnostic refusal; no Native work."""
import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p
from experiments.flat_class_parity_v1 import driver as d

class DiagnosticProofControls(unittest.TestCase):
    def test_exact_retained_control_reaches_specific_partition_class_mismatch(self):
        result=d.mismatch(*d.negative_inputs())
        self.assertTrue(result['refused'])
        self.assertEqual(result['kind'],'ClassIdentityMismatch')
        self.assertIn("SCH='CRITICAL,POWER,Default', PCB='POWER,Default'",result['reason'])

    def test_replaced_netlist_and_rewritten_self_consistent_proof_refuse(self):
        receipt,route,packet=d.fixture.retained()
        with tempfile.TemporaryDirectory(dir=d.ROOT/'.cache')as name:
            copied=Path(name)/'packet';shutil.copytree(receipt.parent,copied)
            net=copied/'final-drc-fields.net';raw=b'; replaced retained payload\n'+net.read_bytes();net.write_bytes(raw)
            proof=copied/'final-drc-fields-proof.json';value=json.loads(proof.read_text());value['netlist_sha256']=hashlib.sha256(raw).hexdigest();proof.write_text(json.dumps(value))
            with patch.object(d.fixture,'retained',return_value=(copied/'route-result.json',route,packet)):
                with self.assertRaisesRegex(p.Rejected,'retained Native netlist/map proof changed'):
                    d.negative_inputs()

    def test_unrelated_schema_failure_never_qualifies_negative(self):
        args=d.negative_inputs()
        with patch.object(d.compare,'derive',side_effect=ValueError('malformed source')):
            with self.assertRaisesRegex(ValueError,'malformed source'):d.mismatch(*args)

    def test_semantically_identical_proof_rewrite_refuses_stale_advertised_hash(self):
        with tempfile.TemporaryDirectory(dir=d.ROOT/'.cache')as name:
            path=Path(name)/'class-parity.json';value={'class_parity_qualified':True}
            path.write_text(json.dumps(value))
            record={'class_parity_sha256':p.sha(path)}
            d.replay_class_proof(path,record,value)
            path.write_text(json.dumps(value,indent=2)+'\n')
            self.assertEqual(json.loads(path.read_text()),value)
            with self.assertRaisesRegex(p.Rejected,'proof bytes or derivation changed'):
                d.replay_class_proof(path,record,value)

if __name__=='__main__':unittest.main()
