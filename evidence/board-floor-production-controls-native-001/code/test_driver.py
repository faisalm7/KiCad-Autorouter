"""Pure acceptance-threat controls; no KiCad/engine process is launched."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('floor_controls_driver',HERE/'driver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class MutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=d.f.read_json(d.POSITIVE);cls.board=Path(cls.receipt['candidate']).read_bytes()
        cls.project=Path(cls.receipt['candidate']).with_suffix('.kicad_pro').read_bytes()
        cls.base=d.sx.parse(cls.board.decode());cls.policy=d.f.read_json(d.POSITIVE.parent/'floor-policy.json')
        cls.original=d.sx.read(Path(cls.receipt['source']));cls.hashes=cls.receipt['source_hashes']
    def test_positive_byte_identity(self):
        board,project,e=d.prepare('positive',self.board,self.project)
        self.assertEqual(board,self.board);self.assertEqual(project,self.project)
        self.assertEqual(e['board_sha256'],d.POSITIVE_CANDIDATE_SHA)
    def test_exact_one_segment_width_only(self):
        b,pro,e=d.prepare('narrow_track',self.board,self.project);t=d.sx.parse(b.decode())
        self.assertEqual(pro,self.project);self.assertEqual(d.p.immutable(t),d.p.immutable(self.base))
        changed=[(a,b) for a,b in zip(d.p.routes(self.base),d.p.routes(t)) if a!=b]
        self.assertEqual(len(changed),1);before,after=changed[0];after=copy.deepcopy(after)
        self.assertEqual(d.uid(after),e['target_uuid']);d.sx.one(after,'width')[1]='0.3';self.assertEqual(before,after)
    def test_exact_one_via_diameter_only(self):
        b,pro,e=d.prepare('small_via',self.board,self.project);t=d.sx.parse(b.decode());changed=[(a,b) for a,b in zip(d.p.routes(self.base),d.p.routes(t)) if a!=b]
        self.assertEqual(len(changed),1);before,after=changed[0];after=copy.deepcopy(after)
        self.assertEqual(d.sx.one(after,'drill'),['drill','0.3']);d.sx.one(after,'size')[1]='1.5';self.assertEqual(before,after);self.assertEqual(pro,self.project)
    def test_only_required_via_removed_both_sides_preserved(self):
        b,pro,e=d.prepare('missing_via',self.board,self.project);t=d.sx.parse(b.decode())
        self.assertEqual(d.p.routes(t),[x for x in d.p.routes(self.base) if x[0]!='via']);self.assertEqual(pro,self.project)
        self.assertEqual(set(e['adjacent_route_uuids']),{'4fb1042b-7184-465a-9b7a-3e49480adcc1','0b45e7e3-4e0d-49fb-aaec-c99c882ae243'})
    def test_only_rule_severity_changed(self):
        b,pro,e=d.prepare('changed_rule',self.board,self.project);self.assertEqual(b,self.board)
        after=json.loads(pro);after['board']['design_settings']['rule_severities']['track_width']='error';self.assertEqual(after,json.loads(self.project));self.assertTrue(e['changed_project'])
    def test_duplicate_target_route_uuid_fails(self):
        t=copy.deepcopy(self.base);r=d.p.routes(t);d.sx.one(r[1],'uuid')[1]=d.sx.one(r[0],'uuid')[1]
        with self.assertRaisesRegex(d.p.Rejected,'ambiguous'):d.prepare('positive',(d.sx.dump(t)+'\n').encode(),self.project)
    def test_unexpected_via_net_fails(self):
        t=copy.deepcopy(self.base);d.sx.one(next(x for x in d.p.routes(t) if x[0]=='via'),'net')[1]='"SIGNAL_B"'
        with self.assertRaisesRegex(d.p.Rejected,'via geometry/net'):d.prepare('positive',(d.sx.dump(t)+'\n').encode(),self.project)
    def test_actual_production_contract_rejects_three_mutations(self):
        # Direct real pure contract, not a substituted validator/native process.
        for case in ('narrow_track','small_via','changed_rule'):
            with self.subTest(case=case),tempfile.TemporaryDirectory(dir=HERE) as tmp:
                root=Path(tmp);out=root/'validation';out.mkdir();candidate=root/'candidate';candidate.mkdir();board=candidate/'fixture.kicad_pcb'
                b,pro,_=d.prepare(case,self.board,self.project);board.write_bytes(b);board.with_suffix('.kicad_pro').write_bytes(pro)
                for name in d.POLICY_FILES:(out/name).write_bytes((d.POSITIVE.parent/name).read_bytes())
                with self.assertRaisesRegex((d.p.Rejected,ValueError),d.CONTRACT_REASONS[case]):d.f.validate_contract(self.original,board,self.hashes,[],self.policy,out)
    def test_positive_and_missing_via_pass_pure_contract_need_real_drc(self):
        for case in ('positive','missing_via'):
            with self.subTest(case=case),tempfile.TemporaryDirectory(dir=HERE) as tmp:
                out=Path(tmp);board=out/'fixture.kicad_pcb';b,pro,_=d.prepare(case,self.board,self.project);board.write_bytes(b);board.with_suffix('.kicad_pro').write_bytes(pro)
                for name in d.POLICY_FILES:(out/name).write_bytes((d.POSITIVE.parent/name).read_bytes())
                d.f.validate_contract(self.original,board,self.hashes,[],self.policy,out)

class PredicateTests(unittest.TestCase):
    def native(self,kind='track_width',target='target',severity='error',opens=0):
        return dict(opens=opens,blocking=0 if opens else 1,warnings=0,exclusions=0,ignored_checks=[],findings=[{'type':kind,'severity':severity,'items':[{'uuid':target}], 'excluded':False}])
    def test_wrong_uuid_not_expected_native_negative(self):
        ok,_=d.diagnostic_pass('narrow_track',self.native(target='wrong'),{'target_uuid':'target'},[]);self.assertFalse(ok)
    def test_warning_not_error_control(self):
        ok,_=d.diagnostic_pass('narrow_track',self.native(severity='warning'),{'target_uuid':'target'},[]);self.assertFalse(ok)
    def test_exclusions_and_ignored_changes_fail(self):
        for key,value in [('exclusions',1),('ignored_checks',[{'key':'track_width'}])]:
            n=self.native();n[key]=value;self.assertFalse(d.diagnostic_pass('narrow_track',n,{'target_uuid':'target'},[])[0])
    def test_missing_via_requires_exact_adjacent_routes(self):
        n=self.native(kind='unconnected_items',target='a',opens=1);e={'adjacent_route_uuids':['a','b']}
        self.assertFalse(d.diagnostic_pass('missing_via',n,e,[])[0]);n['findings'][0]['items'].append({'uuid':'b'})
        self.assertTrue(d.diagnostic_pass('missing_via',n,e,[])[0])
    def test_clean_rule_case_still_requires_production_rejection_elsewhere(self):
        n=dict(opens=0,blocking=0,warnings=0,exclusions=0,ignored_checks=[],findings=[])
        self.assertTrue(d.diagnostic_pass('changed_rule',n,{},[])[0]);n['warnings']=1
        self.assertFalse(d.diagnostic_pass('changed_rule',n,{},[])[0])
    def test_bool_counter_rejected(self):
        n=self.native();n['opens']=False;self.assertFalse(d.diagnostic_pass('narrow_track',n,{'target_uuid':'target'},[])[0])

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.out=Path(self.tmp.name)
        self.record=dict(status='completed',controls_passed=True,within_budget=True)
    def tearDown(self):self.tmp.cleanup()
    def account(self):pass
    def assert_no_positive(self):
        file=self.out/'summary.json'
        if file.exists():self.assertFalse(d.f.read_json(file)['controls_passed'])
    def test_cancel_after_positive_write(self):
        calls=[]
        def stable():
            calls.append(1)
            if len(calls)==2:raise KeyboardInterrupt
        d.publish(self.out,self.record,stable,self.account);self.assert_no_positive()
        self.assertEqual(d.f.read_json(self.out/'summary.json')['status'],'cancelled');self.assertTrue(list(self.out.glob('invalidated-*-summary.json')))
    def test_failed_correction_cannot_leave_positive(self):
        real=d.p.save_json;calls=[]
        def writer(path,data):
            calls.append(1)
            if len(calls)>1:raise OSError('deliberate correction failure')
            real(path,data)
        stable_calls=[]
        def stable():
            stable_calls.append(1)
            if len(stable_calls)>1:raise d.p.Rejected('source stale')
        with patch.object(d.p,'save_json',writer):d.publish(self.out,self.record,stable,self.account)
        self.assertFalse((self.out/'summary.json').exists());self.assertTrue(list(self.out.glob('invalidated-*-summary.json')))
    def test_final_cap_invalidates_positive(self):
        count=[]
        def account():
            count.append(1)
            if len(count)>1:self.record['within_budget']=False
        d.publish(self.out,self.record,lambda:None,account);self.assert_no_positive()
    def test_canonical_tamper_during_final_check(self):
        count=[]
        def stable():
            count.append(1)
            if len(count)==2:
                data=d.f.read_json(self.out/'summary.json');data['invented']=True;d.p.save_json(self.out/'summary.json',data)
        d.publish(self.out,self.record,stable,self.account);self.assert_no_positive()
    def test_signal_during_partial_write_preserved(self):
        real=d.p.save_json;count=[]
        def writer(path,data):
            count.append(1)
            if len(count)==1:
                Path(str(path)+'.partial').write_text('partial');raise KeyboardInterrupt
            real(path,data)
        with patch.object(d.p,'save_json',writer):d.publish(self.out,self.record,lambda:None,self.account)
        self.assert_no_positive();self.assertTrue(list(self.out.glob('invalidated-*-summary.json.partial')))
    def test_duplicate_json_key_rejected(self):
        path=self.out/'bad.json';path.write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(d.p.Rejected,'duplicate'):d.f.read_json(path)

class InvocationTests(unittest.TestCase):
    def test_no_implicit_native_invocation(self):
        with patch.object(d.p,'check_result',side_effect=AssertionError('must not launch')):
            with self.assertRaisesRegex(d.p.Rejected,'explicit'):d.experiment(HERE/'unused')
    def test_symlink_and_existing_directory_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            target=Path(tmp);link=target/'link';link.symlink_to(target,target_is_directory=True)
            with self.assertRaisesRegex(d.p.Rejected,'real path'):d.owned(link)
            with self.assertRaisesRegex(d.p.Rejected,'fresh direct'):d.experiment(target,run_native=True)

if __name__=='__main__':unittest.main()
