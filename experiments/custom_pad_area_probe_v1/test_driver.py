"""Pure geometry/receipt/controller falsifiers. Synthetic observations are NOT native/Java evidence."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import types
import unittest
from unittest import mock
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('area_probe_driver',HERE/'driver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
import checks
EXPECTED=d.fixtures_and_expected()[1]
IP='app.freerouting.geometry.planar.IntPoint'


def observed(split=False):
    cases=[]
    for want in EXPECTED:
        states=[]
        for mode in ('imported','obstacle_false','obstacle_true'):
            pins=[];areas=[];traces=[];graph={i:set() for i in range(1,10 if split else 9)}
            for n,p in enumerate(want['pins'],1):
                row=copy.deepcopy(p);x,y=p['position_um'];row.update(id=n,bounds_um=[x-150,y-150,x+150,y+150],layers=[want['layer']]);pins.append(row)
            refs={p['reference']:p['id'] for p in pins}
            def edge(a,b):graph[a].add(b);graph[b].add(a)
            for n,a in enumerate(want['areas'],5):
                row=copy.deepcopy(a);row.update(id=n,holes=0,obstacle=mode=='obstacle_true',ring_board_integer=copy.deepcopy(a['ring_um']),ring_classes=[IP]*len(a['ring_um']));areas.append(row)
                edge(n,refs[a['reference']])
                if a['reference']=='CONVEX' or want['kind']!='false_hull':edge(n,7)
            for n,t in enumerate(want['tracks'],7):
                row=copy.deepcopy(t);row.update(id=n,layer=want['layer'],corners_um=[t['start_um'],t['end_um']],corner_classes=[IP,IP],
                  area_clearances_um={str(a['id']):250 for a in areas},tree_trace_check_clear=True,tree_overlap_ids=[])
                if t['net']=='FOREIGN' and mode=='obstacle_true' and want['kind']=='foreign_intrusion':
                    row.update(tree_trace_check_clear=False,tree_overlap_ids=[a['id'] for a in areas if a['reference']=='CONCAVE'])
                traces.append(row)
            edge(refs['FOREIGN_A'],8);edge(refs['FOREIGN_B'],8)
            if split:
                a=traces[-1];b=copy.deepcopy(a);b['id']=9
                midpoint=[(x+y)/2 for x,y in zip(a['start_um'],a['end_um'])]
                a['end_um']=list(midpoint);a['corners_um']=[a['start_um'],a['end_um']]
                b['start_um']=list(midpoint);b['corners_um']=[b['start_um'],b['end_um']];traces.append(b)
                graph[refs['FOREIGN_B']].discard(8);graph[8].discard(refs['FOREIGN_B']);edge(8,9);edge(9,refs['FOREIGN_B'])
            for t in traces:t['corners_board_integer']=[[int(n) for n in point] for point in t['corners_um']]
            for item in pins+areas+traces:
                reached={item['id']};todo=[item['id']]
                while todo:
                    for target in graph[todo.pop()]-reached:reached.add(target);todo.append(target)
                item.update(contacts=sorted(graph[item['id']]),connected=sorted(reached))
            nets=[{'name':n,'contains_plane':False,'trace_width_um':500} for n in ('CONTACT','FOREIGN')]
            states.append({'mode':mode,'board_units_per_um':1,'board_origin_dsn_um':[0,0],'ignore_conduction':mode!='obstacle_true','pins':pins,'areas':areas,'traces':traces,'nets':nets,
              'census':{'pins':4,'areas':2,'traces':len(traces),'vias':0,'components':4,'layers':2,'max_net_number':2}})
        cases.append({'case':want['case'],'status':'observed','input_sha256':want['derived_sha256'],'parser_warnings':[],'states':states})
    return {'schema':1,'scope':'owned_area_contact_import_only','units':'micrometres','routing_executed':False,'native_executed':False,'cases':cases}


class Controls(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='test-scratch-');self.out=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def record(self):return {'status':'completed','observations_complete':True,'expected_observations_match':True,'routing_accepted':False,'custom_pad_support_qualified':False}
    def account(self):pass
    def remaining(self):return 59.0
    def test_static_native_basis_derivation_and_protocol(self):
        inputs,exp=d.fixtures_and_expected();p=d.decode(d.content(HERE/'PROTOCOL.json'))
        self.assertEqual(p['expected'],exp);self.assertEqual(p['case_ids'],list(d.IDS))
        self.assertEqual(p['input_sha256'],{k:d.sha(v) for k,v in inputs.items()})
        self.assertTrue(all(v['net_targets']=={'CONTACT':{'width_um':500,'clearance_um':250},'FOREIGN':{'width_um':500,'clearance_um':250}} for v in exp))
    def test_whole_and_split_synthetic_geometry_preserved(self):
        for split in (False,True):self.assertTrue(all(x['expected_observation_matches'] for x in checks.validate(observed(split),EXPECTED)))
    def test_trace_union_rejects_gap_overlap_excursion_wrong_width_layer_net(self):
        want=EXPECTED[2];state=observed(True)['cases'][2]['states'][-1]
        original=[t for t in state['traces'] if t['net']=='FOREIGN'];target=want['tracks'][1]
        for kind in ('gap','overlap','excursion','width','layer','net','rational'):
            pieces=copy.deepcopy(original)
            if kind in ('gap','overlap'):
                y=pieces[1]['start_um'][1]+(1 if kind=='gap' else -1);pieces[1]['start_um'][1]=y;pieces[1]['corners_um'][0][1]=y
            elif kind=='excursion':pieces[1]['corners_um'].insert(1,[pieces[1]['start_um'][0]+1,pieces[1]['start_um'][1]]);pieces[1]['corner_classes'].insert(1,IP)
            elif kind=='width':pieces[1]['width_um']=499
            elif kind=='layer':pieces[1]['layer']='bottom_layer'
            elif kind=='net':pieces[1]['net']='CONTACT'
            else:pieces[1]['corner_classes'][0]='app.freerouting.geometry.planar.RationalPoint'
            with self.subTest(kind=kind):self.assertFalse(checks.exact_trace_union(pieces,target,want['layer']))
    def test_reciprocal_contact_and_false_hull_falsifiers(self):
        for kind in ('one_way','false_hull','plane','shortcuts'):
            value=observed();state=value['cases'][1]['states'][-1]
            if kind=='one_way':state['pins'][0]['contacts']=[]
            elif kind=='false_hull':
                area=next(a for a in state['areas'] if a['reference']=='CONCAVE');area['contacts'].append(7);state['traces'][0]['contacts'].append(area['id'])
            elif kind=='plane':state['nets'][0]['contains_plane']=True
            else:state['pins'][0]['connected'].append(state['pins'][1]['id'])
            with self.subTest(kind=kind):self.assertFalse(checks.validate(value,EXPECTED)[1]['expected_observation_matches'])
    def test_clearance_width_foreign_check_are_independent_obligations(self):
        for kind in ('clearance','width','unblocked','wrong_obstacle'):
            value=observed();state=value['cases'][2]['states'][-1]
            if kind=='clearance':state['traces'][1]['area_clearances_um']['5']=0
            elif kind=='width':state['nets'][0]['trace_width_um']=250
            elif kind=='unblocked':state['traces'][1]['tree_trace_check_clear']=True
            else:state['traces'][1]['tree_overlap_ids']=[6]
            with self.subTest(kind=kind):self.assertFalse(checks.validate(value,EXPECTED)[2]['expected_observation_matches'])
    def test_unexpected_bounded_census_is_retained_mismatch(self):
        value=observed();state=value['cases'][0]['states'][-1];state['census']['vias']=1
        row=checks.validate(value,EXPECTED)[0];self.assertFalse(row['expected_observation_matches']);self.assertEqual(row['states'][-1]['observed_census']['traces'],2)
    def test_missing_case_and_import_failure_are_not_success(self):
        for mutate in (lambda x:x['cases'].pop(),lambda x:x['cases'][0].update(status='failed',census={'pins':100}),lambda x:x.update(native_executed=True)):
            v=observed();mutate(v)
            with self.assertRaises(ValueError):checks.validate(v,EXPECTED)
    def test_bounded_files_symlinks_and_strict_json(self):
        p=self.out/'file';p.write_bytes(b'1234')
        with self.assertRaises(ValueError):d.content(p,3)
        (self.out/'link').symlink_to(p)
        with self.assertRaises(ValueError):d.inventory(self.out)
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}'):
            with self.assertRaises(ValueError):d.decode(raw)
    def test_positive_publication(self):
        result=d.publish(self.out,self.record(),lambda:None,self.account,self.remaining)
        self.assertTrue(result['observations_complete']);self.assertEqual(d.decode(d.content(self.out/'summary.json')),result)
    def test_final_canonical_inmemory_and_cap_invalidation(self):
        for kind in ('canonical','memory','cap'):
            out=self.out/kind;out.mkdir();record=self.record()
            def stable():
                if (out/'summary.json').exists():
                    if kind=='canonical':d.write(out/'summary.json',{'observations_complete':True})
                    elif kind=='memory':record['routing_accepted']=True
            def remaining():
                if kind=='cap':raise TimeoutError('final cap')
                return 59
            result=d.publish(out,record,stable,self.account,remaining)
            self.assertFalse(result['observations_complete']);self.assertFalse(result['routing_accepted'])
    def test_signals_and_failed_invalidation(self):
        for sig in (signal.SIGINT,signal.SIGTERM):
            out=self.out/str(sig);out.mkdir();old={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
            def stable():
                if (out/'summary.json').exists():os.kill(os.getpid(),sig)
            with d.cancellation():result=d.publish(out,self.record(),stable,self.account,self.remaining)
            self.assertEqual(result['status'],'cancelled');self.assertEqual(old,{s:signal.getsignal(s) for s in old})
        out=self.out/'failed';out.mkdir();original=d.write;calls=0
        def write(path,record):
            nonlocal calls
            calls+=1
            if calls>1:raise OSError('disk error')
            return original(path,record)
        def stable():
            if (out/'summary.json').exists():raise KeyboardInterrupt('after positive')
        with mock.patch.object(d,'write',side_effect=write):result=d.publish(out,self.record(),stable,self.account,self.remaining)
        self.assertFalse(result['observations_complete']);self.assertFalse((out/'summary.json').exists())
    def test_whole_flow_stage_freeze_and_late_material_falsifiers(self):
        realroot=d.ROOT
        for variant in ('unchanged','after_parse','late_source','late_observation','late_input','late_class','late_process','late_native'):
            with self.subTest(variant=variant):
                root=self.out/variant;root.mkdir();(root/'.runs').mkdir();helper=root/'experiments/custom_pad_area_probe_v1';helper.mkdir(parents=True)
                for name in d.HELPERS:(helper/name).write_bytes((HERE/name).read_bytes())
                with mock.patch.object(d,'ROOT',realroot):paths=[p for p in d.source_paths() if not p.is_relative_to(HERE)]
                for path in paths:
                    target=root/path.relative_to(realroot);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
                (root/'.git/refs/heads/rebuild').mkdir(parents=True);(root/'.git/HEAD').write_text('ref: refs/heads/rebuild/local-test\n');(root/'.git/refs/heads/rebuild/local-test').write_text('1'*40+'\n')
                p=d.decode(d.content(helper/'PROTOCOL.json'));(root/'tools').mkdir()
                for name in p['tools']:
                    path=root/'tools'/name;path.write_bytes(b'tool');p['tools'][name]={'path':str(path),'bytes':4,'sha256':d.sha(b'tool')}
                d.write(helper/'PROTOCOL.json',p);batch=root/'.runs/output'
                def git(argv,**kwargs):return types.SimpleNamespace(stdout=(root/argv[2].split(':',1)[1]).read_bytes())
                def worker(argv,*,cwd,log,**kwargs):
                    self.assertEqual(argv[:3],d.SANDBOX);log.write_bytes(b'PURE MOCK STAGE; no Java executed\n')
                    if log.name=='compile.log':(batch/'classes/AreaContactProbe.class').write_bytes(b'fake compiled artifact')
                    else:d.write(batch/'observations.json',observed())
                    return {'status':'success','exit_code':0,'cleanup_complete':True,'pid':123,'argv':argv,'log':str(log)}
                actual_validate=d.validate_observation;actual_content=d.content;mutated=False
                def validate(value,expected):
                    result=actual_validate(value,expected)
                    if variant=='after_parse':(batch/'observations.json').write_bytes(b'changed after bounded parse')
                    return result
                def content(path,*args,**kwargs):
                    nonlocal mutated
                    if (batch/'summary.json').exists() and not mutated and Path(path)==root/'.git/refs/heads/rebuild/local-test':
                        targets={'late_source':helper/'driver.py','late_observation':batch/'observations.json','late_input':batch/'inputs/front0-positive.dsn','late_class':batch/'classes/AreaContactProbe.class','late_process':batch/'import-process.json','late_native':root/d.derive.BASIS/'front0-positive/custom-pads.json'}
                        if variant in targets:
                            target=targets[variant];target.write_bytes(target.read_bytes()+b'\n');mutated=True
                    return actual_content(path,*args,**kwargs)
                with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'HERE',helper),mock.patch.object(d.sys,'executable',str(root/'tools/python')),mock.patch.object(d.subprocess,'run',side_effect=git),mock.patch.object(d.runner,'run',side_effect=worker),mock.patch.object(d,'validate_observation',side_effect=validate),mock.patch.object(d,'content',side_effect=content):
                    result=d.experiment(batch)
                self.assertEqual(result['observations_complete'],variant=='unchanged',result.get('error'));self.assertFalse(result['routing_accepted']);self.assertFalse(result['custom_pad_support_qualified'])
                self.assertEqual(d.decode(actual_content(batch/'summary.json'))['observations_complete'],variant=='unchanged')

if __name__=='__main__':unittest.main(verbosity=2)
