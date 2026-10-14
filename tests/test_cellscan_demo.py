"""Authored fixed-six-file packet controls; no GET/native/cache dependencies."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest import mock
from scripts import fetch_led_demo as demo

class CellScanDemoControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=demo.ROOT/'tests',prefix='cellscan-demo-test-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        # Same owned material/synthetic-response scaffolding as Analog controls.
        for name in (*demo.MATERIAL,*demo.ARC_MATERIAL):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((demo.ROOT/name).read_bytes())
        self.public=copy.deepcopy(demo.CELL_SCAN_PROFILE);self.cfg=copy.deepcopy(self.public);self.payloads={};self.requests=[]
        for row in self.cfg['rows']:
            prefix=('authored synthetic CellScan '+row['source_path']+'\n').encode();raw=prefix+b'x'*(row['bytes']-len(prefix));self.payloads[row['source_path']]=raw
            row['git_blob_sha1']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if 'sha256' in row:row['sha256']=hashlib.sha256(raw).hexdigest()
        patch=mock.patch.object(demo,'CELL_SCAN_PROFILE',self.cfg);patch.start();self.addCleanup(patch.stop)
        self.out=self.root/'.data/cellscan-demo-001'
    def transport(self,row,record,path,allowance,remaining):
        remaining();self.requests.append(row['source_path']);raw=self.payloads[row['source_path']]
        with path.open('xb') as stream:stream.write(raw)
        record.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw),status='response_received',http_status=200,wall_seconds=0.0);return raw
    def fetch(self):return demo.fetch_demo('.data/cellscan-demo-001',profile_id='cellscan',fetch=True,root=self.root,transport=self.transport)
    def test_fixed_profile_plan_and_unchanged_old_limits(self):
        self.assertEqual(self.public['commit'],'628c8a7d80f9de07c24d86102dfca9e353c038ce')
        self.assertEqual((self.public['file_count'],self.public['max_requests'],self.public['bytes'],self.public['output_byte_cap']),(6,6,1299230,4*1024**2))
        self.assertEqual(sum('sha256' not in row for row in self.public['rows']),5)
        self.assertEqual(self.public['native_packet_files'],8)
        for row in self.public['rows']:self.assertEqual(row['raw_url'],'https://raw.githubusercontent.com/'+self.public['repository']+'/'+self.public['commit']+'/'+row['source_path'])
        for name in ('led','arcdice','analog-filter'):
            old=demo.fixed_profile(name);self.assertEqual(old.get('max_requests',5),5);self.assertEqual(old.get('output_byte_cap',demo.OUTPUT_BYTES),2*1024**2)
        plan=demo.fetch_demo('.data/cellscan-demo-001',profile_id='cellscan',root=self.root,transport=lambda *a:self.fail('plan fetched'))
        self.assertEqual((plan['planned_files'],plan['planned_bytes'],plan['network_requests']),(6,1299230,0));self.assertFalse((self.root/'.data').exists())
    def test_six_authored_payloads_derive_missing_sha_and_preserve_eight_notices(self):
        result=self.fetch();self.assertEqual((result['status'],result['new_network_requests'],result['received_bytes']),('acquired_unqualified',6,1299230))
        self.assertEqual(result['source_profile'],'fixed six-file public cellscan selection');self.assertFalse(result['accepted']);self.assertFalse(result['native_accepted']);self.assertTrue(result['within_budget'])
        for name,raw in self.payloads.items():self.assertEqual((self.out/'project'/name).read_bytes(),raw)
        raw=demo.verify_project(self.out/'project',profile_id='cellscan');packet=demo.verify_project(self.out/'native-project',profile_id='cellscan',native_packet=True)
        self.assertEqual((raw['file_count'],raw['bytes']),(6,1299230));self.assertEqual((packet['file_count'],packet['bytes']),(8,1305082))
        for name,origin in self.cfg['native_packet_notice_copies'].items():self.assertEqual((self.out/'native-project'/name).read_bytes(),self.payloads[origin])
        base,files=demo.capture_native_source('cellscan',root=self.root);self.assertEqual(len(files),8)
        for name,content in self.payloads.items():self.assertEqual(raw['files'][name]['sha256'],hashlib.sha256(content).hexdigest())
    def test_same_size_wrong_git_blob_with_absent_sha_refuses_response(self):
        name='README.md';raw=self.payloads[name];self.payloads[name]=b'z'+raw[1:]
        result=self.fetch();self.assertEqual(result['status'],'failed');self.assertFalse(result['source_files_exact']);self.assertIn('payload hash',result['first_failure']);self.assertFalse((self.out/'native-project').exists())
    def test_source_drift_extra_file_and_empty_directory_refuse(self):
        self.fetch();project=self.out/'project';name='hardware/CellScan_Schematic.kicad_pcb';path=project/name;old=path.read_bytes();path.write_bytes(b'z'+old[1:])
        with self.assertRaises(ValueError):demo.verify_project(project,profile_id='cellscan')
        path.write_bytes(old);extra=project/'hardware/extra.txt';extra.write_bytes(b'extra')
        with self.assertRaises(ValueError):demo.verify_project(project,profile_id='cellscan')
        extra.unlink();(project/'hardware/empty').mkdir()
        with self.assertRaises(ValueError):demo.verify_project(project,profile_id='cellscan')
    def test_creator_notice_drift_refuses_capture_without_staging(self):
        self.fetch();path=self.out/'native-project/hardware/_licenses/creator/README.md';raw=path.read_bytes();path.write_bytes(b'z'+raw[1:]);before=demo.shared.inventory(self.root)
        with self.assertRaises(ValueError):demo.capture_native_source('cellscan',root=self.root)
        self.assertEqual(demo.shared.inventory(self.root),before)
    def test_benchmark_selection_is_exact_readonly_and_has_no_fallback(self):
        from scripts import experiment_quality as q
        self.fetch();before=demo.shared.inventory(self.root)
        with mock.patch.object(q.c,'ROOT',self.root):
            board,family=q.selected_source('cellscan')
            self.assertEqual(board,self.out/'native-project/hardware/CellScan_Schematic.kicad_pcb')
            self.assertEqual(family,'cellscan-two-layer-development-exposed')
            self.assertEqual(demo.shared.inventory(self.root),before)
            raw=board.read_bytes();board.write_bytes(b'z'+raw[1:])
            with self.assertRaises(ValueError):q.selected_source('cellscan')
    def test_count_request_mismatch_precedes_output_or_transport(self):
        for key in ('file_count','max_requests'):
            old=self.cfg[key];self.cfg[key]=5
            with self.assertRaises(ValueError):self.fetch()
            self.assertFalse((self.root/'.data').exists());self.assertEqual(self.requests,[]);self.cfg[key]=old
    def test_two_mib_cap_does_not_silently_admit_six_response_packet(self):
        self.cfg['output_byte_cap']=2*1024**2
        with self.assertRaises(ValueError):self.fetch()
        self.assertFalse((self.out/'result.json').exists() and demo.publication.read_json(self.out/'result.json').get('status')=='acquired_unqualified')

if __name__=='__main__':unittest.main()
