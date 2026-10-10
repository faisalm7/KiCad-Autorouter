"""Independent bounded pure controls; never native/engine execution."""
from pathlib import Path
import copy,hashlib,json,sys,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'snapshot-001'))
from autorouter import board_floor as g, floor_route as f, pipeline as p, sexpr as sx
ROOT=HERE.parents[1]
RAW=ROOT/'.runs/board-floor-forced-via-001'

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task=(RAW/'source/fixture.kicad_pcb').read_bytes()
        cls.project=(RAW/'source/fixture.kicad_pro').read_bytes()
        cls.native=json.loads((RAW/'forced-via/native-context.json').read_text());cls.native['obstacles']=[]
        cls.raw=(RAW/'forced-via/native.dsn').read_bytes()
        cls.guided,_=g.transform(cls.raw,cls.native,cls.project,cls.task)
        cls.final=sx.read(RAW/'forced-via/candidate/fixture.kicad_pcb')
        cls.final_native=json.loads((RAW/'forced-via/final-context.json').read_text())
    def test_actual_retained_bytechain(self):
        self.assertEqual(self.guided,(RAW/'forced-via/floor-guided.dsn').read_bytes())
        self.assertEqual(g.adapter_bytes(self.guided,[]),(RAW/'forced-via/task.dsn').read_bytes())
        g.verify_chain(self.raw,self.guided,(RAW/'forced-via/task.dsn').read_bytes(),self.native,self.project,self.task)
    def test_adapter_obstacle_drop_rejected(self):
        n=copy.deepcopy(self.native);n['obstacles']=[{'layer':'F.Cu','kind':'PCB_TEXT','bbox_mm':[1,2,3,4]}]
        with self.assertRaises(ValueError):g.verify_chain(self.raw,self.guided,g.adapter_bytes(self.guided,[]),n,self.project,self.task)
    def test_adapter_geometry_mutation_rejected(self):
        data=g.adapter_bytes(self.guided,[]).replace(b'(width 300)',b'(width 200)',1)
        with self.assertRaises(ValueError):g.verify_chain(self.raw,self.guided,data,self.native,self.project,self.task)
    def test_exact_native_routes(self):
        self.assertGreater(g.audit_native_routes(self.final,self.final_native)['native_route_count'],0)
    def test_native_route_mutations_reject(self):
        for key,value in [('uuid','wrong'),('net','wrong'),('width_nm',1),('start_nm',[0,0]),('layer','B.Cu')]:
            n=copy.deepcopy(self.final_native);row=next(r for r in n['routes'] if r['kind']=='segment')
            if row.get(key)==value: value='F.Cu'
            row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):g.audit_native_routes(self.final,n)
    def test_raw_preferences_not_rewritten(self):
        n=copy.deepcopy(self.native);n['nets'][0]['width_nm']=300000
        with self.assertRaises(ValueError):g.transform(self.raw,n,self.project,self.task)
    def test_receipt_downgrade_rejected(self):
        out=HERE/'policy';out.mkdir(exist_ok=True);(out/'floor-policy.json').write_text('{}')
        base={'schema':2,'input_policy':f.POLICY,'adapter':'both','scope':'whole_board_unlocked_routing','baseline':'B1'}
        self.assertEqual(f.receipt_policy(base,out),f.POLICY)
        for key,value in [('schema',1),('input_policy','native'),('baseline','C-prototype'),('adapter','none')]:
            mutated=copy.deepcopy(base);mutated[key]=value
            with self.subTest(key=key),self.assertRaises(p.Rejected):f.receipt_policy(mutated,out)
    def test_cancellation_invalidates_positive(self):
        out=HERE/'publication-cancel';out.mkdir(exist_ok=True)
        report={'accepted':True,'status':'routing_accepted'}
        with patch.object(p,'check_result',side_effect=KeyboardInterrupt):
            f.publish(out,report,lambda:None,lambda:None,lambda:100)
        self.assertFalse(json.loads((out/'result.json').read_text())['accepted'])
    def test_cap_invalidates_positive(self):
        out=HERE/'publication-cap';out.mkdir(exist_ok=True)
        report={'accepted':True,'status':'routing_accepted'}
        with patch.object(p,'check_result',return_value={}):
            f.publish(out,report,lambda:None,lambda:None,lambda:0)
        self.assertFalse(json.loads((out/'result.json').read_text())['accepted'])
    def test_postcheck_receipt_change_invalidates(self):
        out=HERE/'publication-receipt-change';out.mkdir(exist_ok=True)
        report={'accepted':True,'status':'routing_accepted','candidate_sha256':'initial'}
        def check_then_change(path):
            changed=json.loads(path.read_text());changed['candidate_sha256']='changed-after-check'
            p.save_json(path,changed)
            return {}
        with patch.object(p,'check_result',side_effect=check_then_change):
            f.publish(out,report,lambda:None,lambda:None,lambda:100)
        actual=json.loads((out/'result.json').read_text())
        self.assertFalse(actual['accepted'],'canonical positive changed during final readback escaped invalidation')

if __name__=='__main__':unittest.main(verbosity=2)
