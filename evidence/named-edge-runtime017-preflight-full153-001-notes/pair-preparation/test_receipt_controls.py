"""Authored child-receipt regression controls, no real worker or Native test."""
import copy,importlib.util,json,time,unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('owned_pair_controller',HERE/'run-installed-arm.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PairReceiptControls(unittest.TestCase):
    def setUp(self):
        self.folder=HERE/'authored-controls-002'/self._testMethodName;self.folder.mkdir(parents=True)
        self.runtime=self.folder/'runtime';child=self.runtime/'.runs/owned-child';child.mkdir(parents=True)
        self.receipt=child/'result.json';self.pin='a'*64;self.tools={'owned':'synthetic-no-execution'}
        self.row=dict(schema=1,kind='installed-named-edge-pair-arm-v1',arm='016',protocol_sha256=self.pin,
            accepted=False,passed=True,status='completed',tools=self.tools,Native_executed=False)
        self.receipt.write_text(json.dumps(self.row))

    def test_parse_captured_bytes_never_a_second_unbound_row(self):
        self.row['passed']=False;self.receipt.write_text(json.dumps(self.row))
        swapped={**self.row,'passed':True}
        with patch.object(m.f,'read_json',return_value=swapped):
            raw,row,error=m.child_receipt(self.receipt,'016',self.pin)
        self.assertIsNone(error);self.assertFalse(row['passed']);self.assertEqual(json.loads(raw),row)

    def test_wrong_identity_and_nonfinite_or_duplicate_json_never_pass(self):
        for raw in (json.dumps({**self.row,'arm':'017'}),json.dumps({**self.row,'protocol_sha256':'b'*64}),
                json.dumps(self.row)[:-1]+',"passed":true}',json.dumps(self.row)[:-1]+',"cost":NaN}'):
            self.receipt.write_text(raw)
            _,row,error=m.child_receipt(self.receipt,'016',self.pin)
            self.assertIsNone(row);self.assertTrue(error)

    def execute(self,mutation):
        arm=dict(runtime=str(self.runtime),child_output_name='owned-child',runtime_tools=self.tools)
        plan=dict(arms={'016':arm},installed_child_name='owned-test.py',scope='authored-control-no-worker',
            signal_bridge_controller=str(m.ROOT/'.runs/run-native1007-delivery-004.py'))
        calls=[]
        def frozen(*args):
            calls.append(None)
            if len(calls)==2:
                if mutation=='delete':self.receipt.unlink()
                elif mutation=='swap':self.receipt.write_text(json.dumps({**self.row,'passed':False,'status':'failed'}))
            return plan
        def run(job,argv,log,**kwargs):
            log.write_text('AUTHORED CONTROL: no subprocess executed\n')
            return dict(exit_code=0,cancel_requested=False,log_truncated=False)
        m.START=time.monotonic();m.CPU0=m.cpu()
        with patch.object(m,'BASE',self.folder),patch.object(m,'frozen_pair',side_effect=frozen),\
                patch.object(m,'coordinator_python_context',return_value={'owned':'mock'}),\
                patch.object(m.p,'tool_manifest',return_value=self.tools),patch.object(m.gui.CliJob,'run',run):
            code=m.execute(self.folder/'unused-protocol.json',self.pin,'016')
        return code,m.f.read_json(self.folder/'arm016/result.json'),len(calls)

    def test_unchanged_authored_child_can_publish(self):
        code,row,calls=self.execute(None)
        self.assertEqual(code,0);self.assertTrue(row['passed']);self.assertGreaterEqual(calls,2)

    def test_late_deleted_child_cannot_leave_positive_parent(self):
        code,row,calls=self.execute('delete')
        self.assertEqual(code,2);self.assertFalse(row['passed']);self.assertGreaterEqual(calls,2)
        self.assertIn('child receipt raw bytes changed',row['reason'])

    def test_late_swapped_child_cannot_leave_positive_parent(self):
        code,row,calls=self.execute('swap')
        self.assertEqual(code,2);self.assertFalse(row['passed']);self.assertGreaterEqual(calls,2)
        self.assertIn('child receipt raw bytes changed',row['reason'])

if __name__=='__main__':unittest.main()
