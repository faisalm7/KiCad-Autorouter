"""Pure controls only. Synthetic geometry and mocked scheduling do not prove native routing."""
import copy, importlib.util, json, sys, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
from autorouter import thermal as t, thermal_geometry as g

def scene():
    pads=[]
    for uid,center in [('target',[0,0]),('other',[2000000,0])]:
        pads.append(dict(uuid=uid,net_code=100,position_nm=center,logical_terminal=['fp',uid],
             effective_hole=dict(start_nm=center,end_nm=center,width_nm=800000),drill_size_nm=[800000,800000],
             drill_is_round=True,is_pth=True,orientation_degrees=0,
             layers=[dict(id=2,on_layer=True,flash_layer=True,shape_is_circle=True,size_nm=[1400000,1400000],offset_nm=[0,0],shape_position_nm=center)]))
    bodies=[]
    for i,(lo,hi) in enumerate([(-1000000,600000),(900000,3000000)]):
        bodies.append(dict(native_outline_index=i,layer_id=2,zone_uuid='zone',net_code=100,selected=True,holes_nm=[],hole_count=0,native_total_arc_count=0,native_outer_closed=True,native_self_intersecting=False,outer_nm=[[lo,-1000000],[hi,-1000000],[hi,1000000],[lo,1000000]]))
    return dict(schema=1,api_error_count=0,source_unchanged=True,layers=[dict(id=2,canonical='B.Cu')],
                **{'class':dict(width_nm=500000)},native_max_error_nm=10000,target_pad_uuid='target',zone_uuid='zone',net_code=100,pads=pads,
                vias=[dict(uuid='gap',net_code=0,position_nm=[750000,-250000],drill_nm=100000,layer_membership=[2])],bodies=bodies)

def coords(result):return [(p['start_nm'],p['end_nm']) for p in result['path_certificate_candidates']]
def propose(s):return g.propose(s,remaining_seconds=lambda:8,binding_verified=True)

class Geometry(unittest.TestCase):
    def test_positive_rechecked(self):
        s=scene();r=propose(s);self.assertEqual(len(r['path_certificate_candidates']),4)
        self.assertEqual(len(g.verify_proposals(s,r,remaining_seconds=lambda:8)),4)
        self.assertFalse(r['routing_accepted']);self.assertFalse(r['whole_body_certificate_qualified'])
    def test_no_binding(self):
        with self.assertRaises(g.Unsupported):g.propose(scene(),remaining_seconds=lambda:8)
    def test_exhausted_shared_budget(self):
        with self.assertRaises(g.Unsupported):g.propose(scene(),remaining_seconds=lambda:0,binding_verified=True)
    def test_waypoint_operation_cap(self):
        with self.assertRaises(g.Unsupported):g.waypoints(scene()['bodies'][0]['outer_nm'],500000,g.Guard(operations=1))
    def test_all_holes_even_foreign_net_block_bridge(self):
        holes,_=g.drill_census(scene());self.assertFalse(g.bridge_clear([375000,-250000],[1000000,-250000],holes,10000,g.Guard()))
    def test_negative_hole(self):
        s=scene();s['pads'][1]['effective_hole']['width_nm']=-1
        with self.assertRaises(g.Unsupported):propose(s)
    def test_nonpositive_max_error(self):
        s=scene();s['native_max_error_nm']=0
        with self.assertRaises(g.Unsupported):propose(s)
    def test_offset_drill_rejected_as_target(self):
        s=scene();s['pads'][0]['effective_hole']['start_nm']=[1,0];s['pads'][0]['effective_hole']['end_nm']=[1,0]
        with self.assertRaises(g.Unsupported):propose(s)
    def test_slot_rejected(self):
        s=scene();s['pads'][1]['drill_is_round']=False
        with self.assertRaises(g.Unsupported):propose(s)
    def test_target_net(self):
        s=scene();s['pads'][0]['net_code']=999
        with self.assertRaises(g.Unsupported):propose(s)
    def test_body_layer(self):
        s=scene();s['bodies'][0]['layer_id']=0
        with self.assertRaises(g.Unsupported):propose(s)
    def test_duplicate_uuid(self):
        s=scene();s['pads'].append(copy.deepcopy(s['pads'][0]))
        with self.assertRaises(g.Unsupported):propose(s)
    def test_same_logical_terminal_not_destination(self):
        s=scene();s['pads'][1]['logical_terminal']=s['pads'][0]['logical_terminal']
        self.assertFalse(propose(s)['path_certificate_candidates'])
    def test_renaming_invariant(self):
        s=scene();base=coords(propose(s));s['target_pad_uuid']='PWR_A';s['zone_uuid']='Z2'
        for i,pad in enumerate(s['pads']):pad['uuid']='PWR_A' if i==0 else 'RETURN_B';pad['logical_terminal']=['NEW',str(i)]
        for b in s['bodies']:b['zone_uuid']='Z2';b['native_outline_index']+=5
        self.assertEqual(base,coords(propose(s)))
    def test_reversed_serialization_invariant(self):
        s=scene();base=coords(propose(s));s['bodies'].reverse()
        for b in s['bodies']:b['outer_nm'].reverse()
        self.assertEqual(base,coords(propose(s)))
    def test_rotation_translation_invariant(self):
        s=scene();base=coords(propose(s));transform=lambda p:[-p[1]+7000000,p[0]+3000000]
        for p in s['pads']:
            p['position_nm']=transform(p['position_nm']);p['orientation_degrees']+=90
            for key in ('start_nm','end_nm'):p['effective_hole'][key]=transform(p['effective_hole'][key])
            for layer in p['layers']:layer['shape_position_nm']=transform(layer['shape_position_nm'])
        for v in s['vias']:v['position_nm']=transform(v['position_nm'])
        for b in s['bodies']:b['outer_nm']=[transform(p) for p in b['outer_nm']]
        self.assertEqual([(transform(a),transform(b)) for a,b in base],coords(propose(s)))
    def test_forged_proposal_net(self):
        s=scene();r=propose(s);r['path_certificate_candidates'][0]['net_code']=999
        with self.assertRaises(g.Unsupported):g.verify_proposals(s,r,remaining_seconds=lambda:8)
    def test_forged_path_through_drill(self):
        s=scene();r=propose(s);r['path_certificate_candidates'][0]['source_copper_path_nm'].insert(1,[0,0])
        with self.assertRaises(g.Unsupported):g.verify_proposals(s,r,remaining_seconds=lambda:8)
    def test_concavity_crossing(self):
        poly=[[0,0],[100,0],[100,100],[70,100],[70,30],[30,30],[30,100],[0,100]]
        self.assertFalse(g.certified_leg([15,80],[85,80],poly,[],1,g.Guard()))
    def test_exact_margin_tangent_rejected(self):
        poly=[[0,0],[100,0],[100,100],[0,100]]
        self.assertFalse(g.certified_leg([10,10],[90,10],poly,[],10,g.Guard()))
        self.assertTrue(g.certified_leg([11,11],[89,11],poly,[],10,g.Guard()))
    def test_hole_centerline_crossing(self):
        self.assertFalse(g.certified_leg([20,50],[80,50],[[0,0],[100,0],[100,100],[0,100]],[dict(center=[50,50],radius=5)],1,g.Guard()))

class Controls(unittest.TestCase):
    def finding(self):return dict(type='starved_thermal',severity='error',items=[dict(uuid='pad'),dict(uuid='zone')])
    def native(self):return dict(opens=0,blocking=1,warnings=0,exclusions=0,ignored_checks=[],findings=[self.finding()])
    def test_sole_positive(self):self.assertEqual(t.sole_thermal(self.native()),self.finding())
    def test_other_critical_warning_rejected(self):
        n=self.native();n['warnings']=1;n['findings'].append(dict(type='padstack',severity='warning',items=[]));self.assertIsNone(t.sole_thermal(n))
    def test_exclusions_rejected(self):
        n=self.native();n['exclusions']=1;self.assertIsNone(t.sole_thermal(n))
    def test_boolean_counter_rejected(self):
        n=self.native();n['opens']=False;self.assertIsNone(t.sole_thermal(n))
    def test_native_uses_project_package_and_refuses_changed_capture(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp);capture=root/'native.py';live=ROOT/'autorouter/native.py'
            capture.write_bytes(live.read_bytes())
            job=t._SharedJob(SimpleNamespace(steps=[]),root/'job',lambda:4,capture)
            with patch.object(job,'step',return_value={'status':'success'}) as launch:
                job.native('map','netclasses',root/'board',root/'map')
                self.assertEqual(launch.call_args.args[1],[t.cfg.PYTHON,'-B',live,'netclasses',root/'board',root/'map'])
                launch.reset_mock();capture.write_text('changed')
                with self.assertRaises(t.p.Rejected):job.native('map','netclasses',root/'board',root/'map')
                launch.assert_not_called()
    def test_child_receipts_success_error_cancel_once(self):
        for error in (None,t.p.Rejected('failure'),KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__),tempfile.TemporaryDirectory(dir=HERE) as tmp:
                parent=SimpleNamespace(steps=[]);job=t._SharedJob(parent,Path(tmp)/'job',lambda:4,Path(tmp)/'native.py')
                def fake(self,name,argv,allowed):
                    self.steps.append({'name':name,'status':'cancelled' if isinstance(error,KeyboardInterrupt) else 'success'})
                    self.assertion=argv[:3]
                    if error:raise error
                    return self.steps[-1]
                with patch.object(t.p.Job,'step',fake):
                    if error:
                        with self.assertRaises(type(error)):job.step('probe',['python','worker'])
                    else:job.step('probe',['python','worker'])
                self.assertEqual(len(parent.steps),1);self.assertIs(parent.steps[0],job.steps[0]);self.assertEqual(job.assertion[:2],['/usr/bin/sandbox-exec','-p'])
                self.assertNotIn('PYTHONPATH',job.env);self.assertEqual(job.env['PYTHONNOUSERSITE'],'1')
    def test_child_does_not_launch_when_cpu_exhausted(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            parent=SimpleNamespace(steps=[]);budget=[4];job=t._SharedJob(parent,Path(tmp)/'job',lambda:budget[0],Path(tmp)/'native.py');budget[0]=0
            with patch.object(t.p.Job,'step') as run:
                with self.assertRaises(t.p.Rejected):job.step('probe',[])
                run.assert_not_called();self.assertEqual(parent.steps,[])
    def test_map_binding_even_if_outer_audit_is_noop(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            board=Path(tmp)/'board.kicad_pcb';board.write_text('b');board.with_suffix('.kicad_pro').write_text('p')
            data=dict(source=str(board),board_sha256=t.p.sha(board),project_sha256=t.p.sha(board.with_suffix('.kicad_pro')),board_saved=False)
            with patch.object(t.p,'audit_candidate_netclasses',return_value=None):
                t._audit_map(board,[],data);data['board_sha256']='stale'
                with self.assertRaises(t.p.Rejected):t._audit_map(board,[],data)
    def test_publication_invalidates_after_positive_write(self):
        for error in (OSError('disk'),KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__),tempfile.TemporaryDirectory(dir=HERE) as tmp:
                root=Path(tmp);result=dict(validation_passed=True,candidate='x',candidate_sha256='x');calls=[0]
                def recheck():
                    calls[0]+=1
                    if calls[0]==2:raise error
                if isinstance(error,KeyboardInterrupt):
                    with self.assertRaises(KeyboardInterrupt):t._publish_result(root,result,lambda:None,recheck,lambda:1)
                else:t._publish_result(root,result,lambda:None,recheck,lambda:1)
                self.assertFalse(json.loads((root/'repair.json').read_text())['validation_passed']);self.assertIsNone(result['candidate_sha256'])
                self.assertEqual(len(list(root.glob('invalidated-*-repair.json'))),1)
    def test_partial_write_failure_preserved_and_invalidated(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp);save=t.p.save_json;calls=[0];result=dict(validation_passed=True,candidate='x')
            def failing(path,data):
                calls[0]+=1
                if calls[0]==1:
                    (root/'repair.json.partial').write_text(json.dumps(data));raise OSError('disk simulation')
                return save(path,data)
            with patch.object(t.p,'save_json',failing):t._publish_result(root,result,lambda:None,lambda:None,lambda:1)
            self.assertFalse(json.loads((root/'repair.json').read_text())['validation_passed']);self.assertEqual(len(list(root.glob('invalidated-*.partial'))),1)
    def test_failed_invalidation_leaves_no_positive_canonical(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp);save=t.p.save_json;calls=[0];result=dict(validation_passed=True,candidate='x')
            def failing(path,data):
                calls[0]+=1
                if calls[0]>1:raise OSError('disk still unavailable')
                return save(path,data)
            with patch.object(t.p,'save_json',failing):
                with self.assertRaises(OSError):t._publish_result(root,result,lambda:None,lambda:None,lambda:0)
            self.assertFalse((root/'repair.json').exists());self.assertFalse(result['validation_passed'])
    def test_input_symlink_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp);(root/'real').write_text('x');(root/'link').symlink_to(root/'real')
            with self.assertRaises(t.p.Rejected):t._owned(root/'link',ROOT)

if __name__=='__main__':unittest.main(verbosity=2)
