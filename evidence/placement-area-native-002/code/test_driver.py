"""Pure counterfactual fixture/binding/publication controls; no native calls."""
import copy,importlib.util,json,sys,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(HERE),str(ROOT)];sys.dont_write_bytecode=True
import driver as d
import fixture_recipe as r
import support as s

class CounterfactualTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=d.baseline()
 def prepare(self,case):
  row=self.rows[case];source=Path(row['source']);return source,r.prepare(case,source.read_bytes(),row['expected'])
 def test_only_genuine_placement_nodes_removed(self):
  for case in r.CASES:
   with self.subTest(case=case):
    source,(data,expected,removed)=self.prepare(case);old=d.sx.read(source);new=d.sx.parse(data.decode())
    self.assertEqual(d.p.routes(old),d.p.routes(new));self.assertEqual(len(removed),2 if case=='mixed' else 1)
    for a,b in zip(d.sx.children(old,'zone'),d.sx.children(new,'zone')):
     uid=d.sx.unquote(d.sx.one(a,'uuid')[1]);prohibited=any(x['uuid']==uid for x in removed)
     if prohibited:
      self.assertIsNone(d.sx.one(b,'placement'));self.assertEqual(b,[x for x in a if not isinstance(x,list) or x[0]!='placement'])
      observed=next(x for x in expected['zones'] if x['uuid']==uid);self.assertEqual(observed['placement_source'],'');self.assertIs(observed['placement_enabled'],False);self.assertEqual(observed['placement_source_type'],'SHEETNAME')
     else:self.assertEqual(a,b)
 def test_source_change_fails_before_recipe(self):
  row=self.rows['track_prohibited'];source=Path(row['source']);raw=source.read_bytes()
  with self.assertRaises(d.p.Rejected):r.prepare('track_prohibited',raw+b' ',row['expected'])
 def test_wrong_original_placement_metadata_rejected_even_rebound_hash(self):
  row=copy.deepcopy(self.rows['track_prohibited']);raw=Path(row['source']).read_bytes().replace(b'/Diagnostic/',b'/Changed/');row['expected']['board_sha256']=d.hashlib.sha256(raw).hexdigest()
  with self.assertRaises(d.p.Rejected):r.prepare('track_prohibited',raw,row['expected'])
 def test_omission_does_not_mean_valid_constraint(self):
  for case,row in self.rows.items():
   native=row['native'];self.assertTrue(d.omission_expected(native,native));self.assertFalse(d.native_expected(case,native,row['expected'],native['ignored_checks'])[0])
 def test_real_targeted_rejection_is_not_omission(self):
  row=self.rows['track_prohibited'];native=copy.deepcopy(row['native']);native['blocking']=1;native['findings']=[{'type':'items_not_allowed','severity':'error','items':[{'uuid':row['expected']['prohibited_target_uuids'][0]}]}]
  self.assertFalse(d.omission_expected(native,row['native']));self.assertTrue(d.native_expected('track_prohibited',native,row['expected'],row['native']['ignored_checks'])[0])
 def test_changed_ignored_checks_not_matching_omission(self):
  row=self.rows['track_prohibited'];native=copy.deepcopy(row['native']);native['ignored_checks'].append({'key':'items_not_allowed'});self.assertFalse(d.omission_expected(native,row['native']))
 def test_changed_original_receipt_hash_fails(self):
  with patch.object(d,'SOURCE_SUMMARY_SHA','0'*64):
   with self.assertRaises(d.p.Rejected):d.baseline()
 def test_actual_copied_raw_report_tamper_rejected_before_freeze(self):
  with tempfile.TemporaryDirectory(dir=HERE) as tmp:
   copied=Path(tmp)/'actual001';shutil.copytree(d.FAILED,copied)
   receipt=d.f.read_json(copied/'summary.json')
   receipt['completed_evidence']={str(copied/Path(k).name):v for k,v in receipt['completed_evidence'].items()}
   d.audit_recorded_evidence(copied,receipt)
   report=copied/'track_prohibited/diagnostic-drc.json';original=report.read_bytes();report.write_bytes(original+b' ')
   with self.assertRaisesRegex(d.p.Rejected,'recorded case evidence'):d.audit_recorded_evidence(copied,receipt)
 def test_actual_copied_helper_or_fixture_tamper_rejected(self):
  with tempfile.TemporaryDirectory(dir=HERE) as tmp:
   copied=Path(tmp)/'actual001';shutil.copytree(d.FAILED,copied)
   receipt=d.f.read_json(copied/'summary.json')
   receipt['completed_evidence']={str(copied/Path(k).name):v for k,v in receipt['completed_evidence'].items()}
   for relative in ('code/native_areas.py','fixtures/allowed_placement/fixture.kicad_pcb'):
    with self.subTest(relative=relative):
     file=copied/relative;original=file.read_bytes();file.write_bytes(original+b' ')
     with self.assertRaisesRegex(d.p.Rejected,'recorded .* inventory'):d.audit_recorded_evidence(copied,receipt)
     file.write_bytes(original)
 def test_recorded_population_cannot_redirect_prior_reads(self):
  data=d.f.read_json(d.FAILED/'summary.json');data['completed_evidence']['/unrelated']=data['completed_evidence'].pop(str(d.FAILED/'mixed'))
  with self.assertRaisesRegex(d.p.Rejected,'population'):d.audit_recorded_evidence(d.FAILED,data)
 def test_fresh_native_observation_defaults_required(self):
  source,(data,expected,removed)=self.prepare('track_prohibited');old=copy.deepcopy(self.rows['track_prohibited']['area_observation'])
  with self.assertRaises(d.p.Rejected):r.verify_observation(old,expected)
  old['zones']=copy.deepcopy(expected['zones']);self.assertTrue(r.verify_observation(old,expected)['passed'])
 def test_dsn_semantics_unchanged_after_placement_omission(self):
  for case in r.CASES:
   source,(data,expected,removed)=self.prepare(case);self.assertTrue(r.verify_dsn((d.FAILED/case/'native.dsn').read_bytes(),expected)['passed'])
 def test_current_production_preflight_rejects_fresh_counterfactual(self):
  for case in r.CASES:
   source,(data,expected,removed)=self.prepare(case)
   with tempfile.TemporaryDirectory(dir=HERE) as tmp:
    dest=Path(tmp)/'project';shutil.copytree(source.parent,dest);board=dest/source.name;board.write_bytes(data);scope=d.unsupported(board);self.assertFalse(scope['supported']);self.assertIn('rule-area restrictions',scope['reason'])
 def test_scope_acceptance_cannot_be_silently_skipped(self):
  with patch.object(d.p,'preflight',return_value=['kicad_pcb']):
   with self.assertRaises(d.p.Rejected):d.unsupported(Path('unused'))
 def test_new_native_steps_charge_once(self):
  with tempfile.TemporaryDirectory(dir=HERE) as tmp:
   steps=[];job=s.SharedJob(Path(tmp)/'job',lambda:10,steps)
   def fake(self,*args,**kwargs):self.steps.append({'status':'success','cpu_seconds':1})
   with patch.object(d.p.Job,'step',fake):job.step('fake',['no-execution'])
   self.assertEqual(steps,[{'status':'success','cpu_seconds':1}])

class PublicationTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.out=Path(self.tmp.name);self.record={'status':'completed','controls_passed':True,'within_budget':True}
    def tearDown(self):self.tmp.cleanup()
    def assert_rejected(self):
        file=self.out/'summary.json'
        if file.exists():self.assertFalse(d.f.read_json(file)['controls_passed'])
    def test_cancel_after_positive_and_failed_rewrite_removes_canonical(self):
        stable_calls=[];save_calls=[];real=d.p.save_json
        def stable():
            stable_calls.append(1)
            if len(stable_calls)>1:raise KeyboardInterrupt
        def save(path,value):
            save_calls.append(1)
            if len(save_calls)>1:raise OSError('failed correction')
            real(path,value)
        with patch.object(d.p,'save_json',save):s.publish(self.out,self.record,stable,lambda:None)
        self.assertFalse((self.out/'summary.json').exists());self.assertTrue(list(self.out.glob('invalidated-*-summary.json')))
    def test_summary_mutated_by_final_check_rejects(self):
        calls=[]
        def stable():
            calls.append(1)
            if len(calls)==2:
                value=d.f.read_json(self.out/'summary.json');value['forged']=True;d.p.save_json(self.out/'summary.json',value)
        s.publish(self.out,self.record,stable,lambda:None);self.assert_rejected()
    def test_final_cap_crossing_rejects(self):
        calls=[]
        def account():
            calls.append(1)
            if len(calls)>1:self.record['within_budget']=False
        s.publish(self.out,self.record,lambda:None,account);self.assert_rejected()
    def test_real_partial_receipt_is_retained(self):
        real=d.p.save_json;calls=[]
        def save(path,value):
            calls.append(1)
            if len(calls)==1:Path(str(path)+'.partial').write_text('interrupted');raise KeyboardInterrupt
            real(path,value)
        with patch.object(d.p,'save_json',save):s.publish(self.out,self.record,lambda:None,lambda:None)
        self.assert_rejected();self.assertTrue(list(self.out.glob('invalidated-*-summary.json.partial')))

class InvocationTests(unittest.TestCase):
    def test_no_implicit_native_work(self):
        with patch.object(d.p,'check_result',side_effect=AssertionError('unexpected invocation')):
            with self.assertRaisesRegex(d.p.Rejected,'explicit'):d.experiment(HERE/'unused')
    def test_cancelled_step_cannot_be_treated_as_ordinary_rejection(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            shared=[];job=s.SharedJob(Path(tmp)/'job',lambda:10,shared)
            def cancelled(self,*args,**kwargs):self.steps.append({'status':'cancelled'});raise d.p.Rejected('cancelled child')
            with patch.object(d.p.Job,'step',cancelled):
                with self.assertRaises(KeyboardInterrupt):job.step('fake',['no-executable'])
            self.assertEqual(shared,[{'status':'cancelled'}])

if __name__=='__main__':unittest.main()
