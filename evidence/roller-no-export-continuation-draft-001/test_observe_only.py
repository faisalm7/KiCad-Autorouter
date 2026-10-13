"""Pure native-worker seams; no native imports/processes or shared source edits."""
import copy,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'autorouter/floor_context.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.roller_support_v1 import observe_only as m
from autorouter import sexpr as sx
API=types.SimpleNamespace(LT_SIGNAL=1,LT_JUMPER=2,F_Cu=0,B_Cu=2,PCB_TEXT=type('FakeText',(),{}))
def fp(uid,reference):return types.SimpleNamespace(m_Uuid=types.SimpleNamespace(AsString=lambda:uid),GetReference=lambda:reference)
def native(rows):
    fps=[fp(row['uuid'],row['reference']) for row in rows];pads=[types.SimpleNamespace(GetParentFootprint=lambda owner=owner:owner) for owner,row in zip(fps,rows) for _ in range(row['pad_count'])]
    return types.SimpleNamespace(GetPads=lambda:pads,GetFootprints=lambda:fps,GetDrawings=lambda:[],GetLayerType=lambda layer:1 if layer==0 else 2,GetLayerName=lambda layer:'F.Cu' if layer==0 else 'B.Cu')
class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name);inp=self.out/'input';inp.mkdir();self.board=inp/'fixture.kicad_pcb'
        self.tree=['kicad_pcb',['footprint','"owned"',['uuid','"fp-a"'],['property','"Reference"','"LOGO"']],['footprint','"owned"',['uuid','"fp-b"'],['property','"Reference"','"LOGO"'],['pad','"1"','smd','rect']]]
        sx.write(self.board,self.tree);self.board.with_suffix('.kicad_pro').write_text('{}');self.context=self.out/'context.json';self.diag=self.out/'observation.json';self.rows=m.source_footprints(self.tree);self.calls=[]
    def collect(self,mode,source,output,dsn=None,area_output=None,*,observation_output=None,observer=None):
        self.assertEqual(mode,'final');self.assertIsNone(dsn);self.assertIsNone(area_output);self.assertTrue(callable(observer));self.calls.append(mode)
        board=native(self.rows);a,b=observer(board,API),observer(board,API);before=m.fc.inventory(source.parent)
        context={'mode':mode,'source':str(source),'native_version':'10.0.0','units':'integer nanometres','dsn_sha256':None,'input_hashes_before':before,'input_hashes_after':before,'board_saved':False,'routing_accepted':False}
        output.write_text(json.dumps(context));extra={**context,'floor_context_sha256':m.fc.sha(output),'same_loaded_board':True,'observation_before_export':a,'observation_after_export':b};observation_output.write_text(json.dumps(extra))
    def test_final_no_export_preserves_duplicate_references_and_source(self):
        before=m.fc.inventory(self.board.parent)
        with patch.object(m.fc,'collect',side_effect=self.collect):context,diag=m.collect_only(self.board,self.context,self.diag)
        self.assertEqual(self.calls,['final']);self.assertIsNone(context['dsn_sha256']);self.assertIsNone(diag['dsn_sha256']);self.assertEqual(m.fc.inventory(self.board.parent),before)
        group=diag['observation_before_export']['duplicate_reference_groups'];self.assertEqual(group[0]['reference'],'LOGO');self.assertEqual(len(group[0]['footprints']),2);self.assertFalse(diag['observation_before_export']['dsn_export_attempted'])
    def test_loaded_reference_or_padcount_drift_rejects(self):
        for key,value in [('reference','changed'),('pad_count',2)]:
            rows=copy.deepcopy(self.rows);rows[0][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'native/source'):m.observe(native(rows),API,self.rows)
    def test_duplicate_source_uuid_rejects(self):
        self.tree[2][2][1]='"fp-a"'
        with self.assertRaisesRegex(ValueError,'unique'):m.source_footprints(self.tree)
    def test_missing_original_reference_rejects(self):
        self.tree[1].pop()
        with self.assertRaisesRegex(ValueError,'identity'):m.source_footprints(self.tree)
    def test_nonnull_dsn_or_stale_context_binding_rejects(self):
        def corrupt(*args,**kwargs):
            self.collect(*args,**kwargs);x=json.loads(self.diag.read_text());x['dsn_sha256']='wrong';self.diag.write_text(json.dumps(x))
        with patch.object(m.fc,'collect',side_effect=corrupt),self.assertRaisesRegex(ValueError,'binding'):m.collect_only(self.board,self.context,self.diag)
    def test_missing_same_load_capture_rejects(self):
        def corrupt(*args,**kwargs):
            self.collect(*args,**kwargs);x=json.loads(self.diag.read_text());x['observation_before_export']=None;x['observation_after_export']=None;self.diag.write_text(json.dumps(x))
        with patch.object(m.fc,'collect',side_effect=corrupt),self.assertRaisesRegex(ValueError,'binding'):m.collect_only(self.board,self.context,self.diag)
    def test_source_change_after_shared_collect_rejects(self):
        def corrupt(*args,**kwargs):self.collect(*args,**kwargs);self.board.with_suffix('.kicad_pro').write_text('{"changed":true}')
        with patch.object(m.fc,'collect',side_effect=corrupt),self.assertRaisesRegex(ValueError,'binding'):m.collect_only(self.board,self.context,self.diag)
    def test_real_original_static_census_is23footprints15pads_three_duplicate_groups(self):
        path=ROOT/'.data/corpus-expansion-audit-001/sparkfun__SparkFun_Roller_Encoder_Breakout/Hardware/SparkFun_Roller_Encoder_Breakout.kicad_pcb';rows=m.source_footprints(sx.read(path))
        self.assertEqual((len(rows),sum(r['pad_count'] for r in rows)),(23,15));observed=m.observe(native(rows),API,rows)
        self.assertEqual([r['reference'] for r in observed['duplicate_reference_groups']],['G***','kibuzzard-679465CE','kibuzzard-679465D4'])
        self.assertTrue(all(fp['pad_count']==0 for group in observed['duplicate_reference_groups'] for fp in group['footprints']))
if __name__=='__main__':unittest.main(verbosity=2)
