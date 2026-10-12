"""Small pure source/observer/capture/publication controls; no native process."""
from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.path[:0]=[str(HERE),str(ROOT)];sys.dont_write_bytecode=True
import controls as k,worker as w,driver as d
from autorouter import pipeline as p,sexpr as sx,board_floor as g
BASE=ROOT/'fixtures/smoke'


def fixture(case):
    board,project=k.derive((BASE/'smoke.kicad_pcb').read_bytes(),(BASE/'smoke.kicad_pro').read_bytes(),case)
    tree=sx.parse(board.decode());ident=g.task_pads(tree);codes={'GND':1,'SIGNAL_A':2,'SIGNAL_B':3}
    if case=='assigned_padless':codes[k.PADLESS]=4
    pads=[]
    for fp in sx.children(tree,'footprint'):
        pad=sx.children(fp,'pad')[0];uid=sx.unquote(sx.one(pad,'uuid')[1]);item={'uuid':uid,**ident[uid]};item['netcode']=codes[item['net']];item['position_nm']=[int(float(x)*1000000) for x in sx.one(fp,'at')[1:]];pads.append(item)
    name={'assigned_gnd':'GND','assigned_padless':k.PADLESS,'net_zero':''}[case]
    zone={'uuid':k.ZONE_UUID,'is_copper':True,'is_rule_area':False,'layers':[{'id':2,'name':'B.Cu'}],'netcode':codes.get(name,0),'net':name,
          'pad_count':{'assigned_gnd':2,'assigned_padless':0,'net_zero':None}[case],'outline_nm':[[6000000,6000000],[44000000,6000000],[44000000,34000000],[6000000,34000000]],'closed':True,'holes':0,'arc_count':0}
    observation={'schema':1,'connectivity_build_succeeded':True,'footprint_zone_count':0,'pads':pads,'zones':[zone]}
    context={'pads':copy.deepcopy(pads),'nets':[{'name':name,'netcode':code} for name,code in codes.items()],'routes':[]}
    return board,project,context,observation


class Controls(unittest.TestCase):
    def test_fixed_case_delta_and_identical_rule(self):
        original=sx.read(BASE/'smoke.kicad_pcb');projects=[]
        for case in k.CASES:
            board,project,context,obs=fixture(case);projects.append(project)
            tree=sx.parse(board.decode());zone=sx.children(tree,'zone')[0]
            if case=='net_zero':self.assertIsNone(sx.one(zone,'net'));zone.insert(1,['net','"GND"'])
            else:sx.one(zone,'net')[1]='"GND"'
            self.assertEqual(tree,original);self.assertEqual(k.evaluate(case,board,context,obs)['historical_violation'],case=='assigned_padless')
        self.assertEqual(len(set(projects)),1)
        self.assertEqual(json.loads(projects[0]),{'meta':{'filename':'smoke.kicad_pro','version':1},'board':{'design_settings':{'rule_severities':{'zone_has_empty_net':'error'}}}})
        self.assertEqual(fixture('assigned_gnd')[0],(BASE/'smoke.kicad_pcb').read_bytes())

    def test_wrong_native_count_identity_geometry_or_type_rejects(self):
        mutations=[lambda o:o.update(connectivity_build_succeeded=1),lambda o:o.update(footprint_zone_count=True),
          lambda o:o['zones'][0].update(pad_count=0),lambda o:o['zones'][0].update(netcode=True),lambda o:o['zones'][0].update(uuid='wrong'),
          lambda o:o['zones'][0]['layers'][0].update(id=0),lambda o:o['zones'][0].update(net='SIGNAL_A'),lambda o:o['zones'][0].update(closed=1),
          lambda o:o['zones'][0]['outline_nm'][0].__setitem__(0,6000001),lambda o:o['pads'][0].update(net='WRONG_NET')]
        for mutation in mutations:
            board,_,context,obs=fixture('assigned_gnd');mutation(obs)
            with self.subTest(mutation=repr(mutation)),self.assertRaises((p.Rejected,KeyError)):k.evaluate('assigned_gnd',board,context,obs)
        board,_,context,obs=fixture('assigned_padless');obs['zones'][0]['pad_count']=2
        with self.assertRaises(p.Rejected):k.evaluate('assigned_padless',board,context,obs)
        board,_,context,obs=fixture('net_zero');obs['zones'][0]['pad_count']=0
        with self.assertRaises(p.Rejected):k.evaluate('net_zero',board,context,obs)

    def test_net_identity_and_route_census_rejects(self):
        for mutate in (lambda c:c['nets'].append(copy.deepcopy(c['nets'][0])),lambda c:c['nets'][0].update(netcode=4),lambda c:c['routes'].append({'uuid':'extra'})):
            board,_,context,obs=fixture('assigned_gnd');mutate(context)
            with self.assertRaises(p.Rejected):k.evaluate('assigned_gnd',board,context,obs)
        for code,count in ((True,0),(1,False),(1,-1),(0,0),(1,None)):
            with self.assertRaises(p.Rejected):k.historical_violation(code,count)
        self.assertFalse(k.historical_violation(0,None));self.assertTrue(k.historical_violation(-1,None))

    def test_worker_build_type_and_no_zero_count_call(self):
        for case in k.CASES:
            _,_,_,expected=fixture(case);calls=[]
            def uid(value):return NS(AsString=lambda:value)
            pads=[]
            for row in expected['pads']:
                pads.append(NS(m_Uuid=uid(row['uuid']),GetParentFootprint=lambda r=row:NS(GetReference=lambda:r['reference']),GetNumber=lambda r=row:r['number'],GetNetCode=lambda r=row:r['netcode'],GetNetname=lambda r=row:r['net'],GetPosition=lambda r=row:NS(x=r['position_nm'][0],y=r['position_nm'][1]),IsOnLayer=lambda layer:True))
            z=expected['zones'][0];line=NS(PointCount=lambda:4,CPoint=lambda i:NS(x=z['outline_nm'][i][0],y=z['outline_nm'][i][1]),IsClosed=lambda:True)
            zone=NS(m_Uuid=uid(z['uuid']),GetNetCode=lambda:z['netcode'],GetNetname=lambda:z['net'],GetLayerSet=lambda:NS(Seq=lambda:[2]),IsOnCopperLayer=lambda:True,GetIsRuleArea=lambda:False,Outline=lambda:NS(OutlineCount=lambda:1,COutline=lambda _:line,HoleCount=lambda _:0,ArcCount=lambda:0))
            board=NS(GetFootprints=lambda:[],GetPads=lambda:pads,Zones=lambda:[zone])
            def build(value):self.assertIs(value,board);calls.append('build');return True
            def count(code):self.assertGreater(code,0);calls.append(code);return z['pad_count']
            api=NS(CONNECTIVITY_DATA=lambda:NS(Build=build,GetPadCount=count),F_Cu=0,B_Cu=2,LayerName=lambda layer:'B.Cu')
            self.assertEqual(w.observe(board,api),dict(expected,pads=sorted(expected['pads'],key=lambda r:r['uuid'])))
            self.assertEqual(calls,['build'] if case=='net_zero' else ['build',z['netcode']])
            api.CONNECTIVITY_DATA=lambda:NS(Build=lambda _:1)
            with self.assertRaisesRegex(ValueError,'Boolean'):w.observe(board,api)
            api.CONNECTIVITY_DATA=lambda:NS(Build=lambda _:False)
            with self.assertRaisesRegex(ValueError,'returned false'):w.observe(board,api)

    def test_no_ignored_draft_native_execution(self):
        with patch.object(d,'HERE',ROOT/'.runs/unpromoted-zone-control'),patch.object(d,'ZoneJob') as job:
            with self.assertRaisesRegex(p.Rejected,'promote'):d.experiment(HERE/'must-not-exist',run_native=True)
            job.assert_not_called()
        with patch.object(d,'HERE',ROOT/'experiments/legacy_zone_controls_v1'),patch.object(d,'ZoneJob') as job:
            with self.assertRaisesRegex(p.Rejected,'ROOT --run-native'):d.experiment(HERE/'must-not-exist',run_native=False)
            job.assert_not_called()
        self.assertFalse((HERE/'must-not-exist').exists())

    def test_raw_stage_capture_precedes_caller_parsing(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            out=Path(tmp)/'case';job=d.ZoneJob(out,lambda:30);source=out/'observe-input';source.mkdir();(source/'smoke.kicad_pcb').write_text('owned fake input')
            def fake(argv,**kwargs):
                for name in ('context.json','zones.json','native.dsn'):(out/name).write_text('original raw '+name)
                (out/'observe.log').write_text('owned fake worker')
                return {'status':'success','exit_code':0,'cleanup_complete':True,'argv':argv}
            with patch.object(d,'run',side_effect=fake):job.step('observe',d.observer_argv(out))
            captured=copy.deepcopy(job.captured['observe']);(out/'zones.json').write_text('late change')
            self.assertNotEqual(p.sha(out/'zones.json'),captured['artifacts']['zones.json'])
            self.assertEqual(captured['input'],d.capture(source))
            with self.assertRaisesRegex(p.Rejected,'unexpected'):job.step('observe',['wrong'])

    def test_shared_publication_invalidates_canonical_cap_and_interruption(self):
        for mode in ('positive','late_file','cancel','cap'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory(dir=HERE) as tmp:
                out=Path(tmp);artifact=out/'native.json';artifact.write_text('captured');expected=p.sha(artifact)
                record={'status':'observations_complete','observations_complete':True,**{key:False for key in d.FALSE_FLAGS}}
                def stable():
                    if p.sha(artifact)!=expected:raise p.Rejected('stage changed')
                def account():record.update({key:False for key in d.FALSE_FLAGS})
                def final_size(_):
                    if mode=='late_file':artifact.write_text('mutated in final output scan')
                    if mode=='cancel':raise KeyboardInterrupt
                    return d.LIMIT+1 if mode=='cap' else 1
                with patch.object(d.shared,'size',side_effect=final_size):actual=d.shared.publish(out,record,stable,account,lambda:30)
                self.assertEqual(actual['observations_complete'],mode=='positive')
                self.assertEqual(d.shared.read(out/'summary.json')['observations_complete'],mode=='positive')
                self.assertTrue(all(actual[key] is False for key in d.FALSE_FLAGS))
                self.assertEqual(bool(list(out.glob('invalidated-*'))),mode!='positive')

if __name__=='__main__':unittest.main()
