"""Pure fixture/control/publication tests. No native/engine execution."""
import copy,importlib.util,json,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import driver as d

class Fixture(unittest.TestCase):
    def setUp(self):self.base=d.sx.read(HERE/'fixture/fixture.kicad_pcb')
    def test_original_recipe_and_project_identity(self):
        self.assertEqual(self.base,d.f.original(d.sx.read(d.ROOT/'fixtures/smoke/smoke.kicad_pcb')))
        self.assertEqual(d.p.sha(HERE/'fixture/fixture.kicad_pro'),d.PROJECT_SHA)
        self.assertEqual(d.p.sha(d.PROJECT),d.PROJECT_SHA)
    def test_every_control_preserves_source_geometry_and_net_mapping(self):
        before=d.sx.dump(self.base)
        for case in d.f.CASES:
            candidate,_=d.f.candidate(self.base,case);self.assertEqual(d.p.immutable(candidate),self.base)
            ids=[d.sx.one(n,'uuid')[1] for n in d.p.routes(candidate)];self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(d.sx.dump(self.base),before)
    def test_topology_forces_transition(self):
        result=d.f.force_via_topology(self.base);self.assertEqual(result['net'],'SIGNAL_A');self.assertFalse(result['engine_via_emission_qualified'])
    def test_same_side_not_forced(self):
        for fp in d.sx.children(self.base,'footprint'):
            pad=d.sx.one(fp,'pad');layers=d.sx.one(pad,'layers');layers[1:]=['"F.Cu"','"F.Paste"','"F.Mask"']
        with self.assertRaises(ValueError):d.f.force_via_topology(self.base)
    def test_plated_source_cannot_claim_forced_via(self):
        pad=d.sx.one(d.sx.children(self.base,'footprint')[0],'pad');pad[2]='thru_hole';pad.append(['drill','0.8'])
        with self.assertRaises(ValueError):d.f.force_via_topology(self.base)
    def test_source_zone_or_via_prevents_claim(self):
        for extra in (['zone'],['via']):
            tree=copy.deepcopy(self.base);tree.append(extra)
            with self.assertRaises(ValueError):d.f.force_via_topology(tree)
    def test_clearance_control_has_point_two_copper_gap(self):
        tree,_=d.f.candidate(self.base,'clearance');routes={d.sx.unquote(d.sx.one(n,'uuid')[1]):n for n in d.p.routes(tree)}
        first,second=routes[d.f.uid('A-front')],routes[d.f.uid('B-near')]
        y=lambda n:float(d.sx.one(n,'start')[2]);width=lambda n:float(d.sx.one(n,'width')[1])
        self.assertAlmostEqual(abs(y(first)-y(second))-(width(first)+width(second))/2,.2)
        self.assertEqual(d.sx.one(first,'net')[1],'"SIGNAL_A"');self.assertEqual(d.sx.one(second,'net')[1],'"SIGNAL_B"')
    def test_annulus_control_above_drill_and_diameter_floors(self):
        tree,_=d.f.candidate(self.base,'annulus');via=d.sx.children(tree,'via')[0];diameter=float(d.sx.one(via,'size')[1]);drill=float(d.sx.one(via,'drill')[1])
        self.assertEqual(diameter,1.5);self.assertGreater(drill,.3);self.assertLess((diameter-drill)/2,.3)
    def test_positive_derived_dimensions(self):
        tree,_=d.f.candidate(self.base,'positive')
        context={'derived_nm':{'width_nm':300000,'clearance_nm':300000,'via_diameter_nm':1500000,'via_drill_nm':300000},'floors_nm':{'min_via_annular_width':300000},'nets':[{'name':'SIGNAL_A'},{'name':'SIGNAL_B'}]}
        self.assertEqual(d.g.audit_generated_routes(tree,context)['counts'],{'segment':7,'arc':0,'via':1})
        for case in ('track_width','via_diameter','drill','annulus'):
            with self.assertRaises(ValueError):d.g.audit_generated_routes(d.f.candidate(self.base,case)[0],context)
    def test_no_unknown_case_fallback(self):
        with self.assertRaises(ValueError):d.f.candidate(self.base,'anything')

class Acceptance(unittest.TestCase):
    def native(self,kind='track_width',severity='error',uid=None):
        return {'opens':0,'blocking':int(severity=='error'),'warnings':int(severity=='warning'),'exclusions':0,'ignored_checks':[], 'findings':[{'type':kind,'severity':severity,'items':[{'uuid':uid or d.f.uid('A-front')}]}]}
    def test_invalid_requires_actual_targeted_native_error(self):
        expected=('track_width',[d.f.uid('A-front')]);native=self.native()
        self.assertTrue(d.native_case_pass('track_width',native,expected)[0])
        for bad in (self.native(uid='different'),self.native(kind='clearance'),self.native(severity='warning')):
            self.assertFalse(d.native_case_pass('track_width',bad,expected)[0])
    def test_missing_target_one_of_pair_rejected(self):
        self.assertFalse(d.native_case_pass('clearance',self.native(kind='clearance'),('clearance',[d.f.uid('A-front'),d.f.uid('B-near')]))[0])
    def test_native_failure_unrelated_or_opens_not_success(self):
        n=self.native();n['opens']=1;self.assertFalse(d.native_case_pass('track_width',n,('track_width',[d.f.uid('A-front')]))[0])
    def test_positive_native_rejection_not_hidden(self):
        self.assertFalse(d.native_case_pass('positive',self.native(),None)[0])
        n=self.native();n.update(blocking=0,findings=[]);self.assertTrue(d.native_case_pass('positive',n,None)[0])
    def test_native_route_geometry_and_dimension_tamper(self):
        base=d.sx.read(HERE/'fixture/fixture.kicad_pcb');tree,_=d.f.candidate(base,'positive');node=d.p.routes(tree)[0]
        one=copy.deepcopy(base);one.append(node)
        row={'uuid':d.f.uid('A-front'),'net':'SIGNAL_A','kind':'segment','start_nm':[10000000,10000000],'end_nm':[35000000,10000000],'layer':'F.Cu','width_nm':300000}
        self.assertTrue(d.audit_native_routes(one,{'routes':[row]})['passed'])
        for key,value in [('width_nm',200000),('net','SIGNAL_B'),('start_nm',[10000001,10000000]),('uuid','other')]:
            bad=dict(row);bad[key]=value
            with self.assertRaises(d.p.Rejected):d.audit_native_routes(one,{'routes':[bad]})
    def test_fractional_native_coordinate_not_truncated(self):
        base=d.sx.read(HERE/'fixture/fixture.kicad_pcb');tree,_=d.f.candidate(base,'positive');d.sx.one(d.p.routes(tree)[0],'start')[1]='10.0000005'
        with self.assertRaises(ValueError):d.audit_native_routes(tree,{'routes':[]})

class RuntimeGuards(unittest.TestCase):
    def test_no_native_without_explicit_flag(self):
        with patch.object(d.p,'tool_manifest') as tool:
            with self.assertRaisesRegex(d.p.Rejected,'run-native'):d.experiment(HERE/'not-created','geometry')
            tool.assert_not_called();self.assertFalse((HERE/'not-created').exists())
    def test_shared_child_charge_once_on_success_failure_cancel(self):
        for error in (None,d.p.Rejected('fake'),KeyboardInterrupt()):
            with tempfile.TemporaryDirectory(dir=HERE) as tmp:
                steps=[];job=d.SharedJob(Path(tmp)/'job',lambda:10,steps,HERE)
                def fake(self,name,argv,allowed):
                    self.steps.append({'name':name,'status':'cancelled' if isinstance(error,KeyboardInterrupt) else 'success'})
                    self.assertion=argv
                    if error:raise error
                    return self.steps[-1]
                with patch.object(d.p.Job,'step',fake):
                    if error:
                        with self.assertRaises(type(error)):job.step('test',[])
                    else:job.step('test',[])
                self.assertEqual(len(steps),1);self.assertIs(steps[0],job.steps[0]);self.assertEqual(job.assertion[:2],['/usr/bin/sandbox-exec','-p'])
    def test_shared_exhaustion_prevents_next_process(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            remaining=[10];job=d.SharedJob(Path(tmp)/'job',lambda:remaining[0],[],HERE);remaining[0]=0
            with patch.object(d.p.Job,'step') as execute:
                with self.assertRaises(d.p.Rejected):job.step('x',[])
                execute.assert_not_called()
    def test_engine_reserves_native_finalization(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            job=d.SharedJob(Path(tmp)/'job',lambda:20,[],HERE)
            with patch.object(d.p.Job,'step') as execute:
                with self.assertRaises(d.p.Rejected):job.step('engine',[])
                execute.assert_not_called()
    def test_after_positive_publication_failure_invalidates(self):
        for error in (KeyboardInterrupt(),OSError('fixture write fault')):
            with tempfile.TemporaryDirectory(dir=HERE) as tmp:
                out=Path(tmp);record={'controls_passed':True,'within_budget':True};calls=[0]
                def stable():
                    calls[0]+=1
                    if calls[0]==2:raise error
                d.publish(out,record,stable,lambda:None)
                self.assertFalse(json.loads((out/'summary.json').read_text())['controls_passed']);self.assertTrue(list(out.glob('invalidated-*')))
    def test_partial_and_failed_correction_leave_no_positive_canonical(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            out=Path(tmp);record={'controls_passed':True,'within_budget':True};save=d.p.save_json;calls=[0]
            def fake(path,data):
                calls[0]+=1
                if calls[0]==1:
                    save(path,data);(out/'summary.json.partial').write_text('partial');raise OSError('first')
                raise OSError('correction unavailable')
            with patch.object(d.p,'save_json',fake):
                with self.assertRaises(OSError):d.publish(out,record,lambda:None,lambda:None)
            self.assertFalse((out/'summary.json').exists());self.assertFalse((out/'summary.json.partial').exists());self.assertFalse(record['controls_passed'])
    def test_postpublication_cap_failure_invalidates(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            record={'controls_passed':True,'within_budget':True};count=[0]
            def account():
                count[0]+=1
                if count[0]>1:record['within_budget']=False
            d.publish(Path(tmp),record,lambda:None,account);self.assertFalse(json.loads((Path(tmp)/'summary.json').read_text())['controls_passed'])

if __name__=='__main__':unittest.main(verbosity=2)
