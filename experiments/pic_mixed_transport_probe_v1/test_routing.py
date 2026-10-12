"""Pure lifecycle/transport falsifiers; synthesized routes are never solver evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from experiments.pic_mixed_transport_probe_v1 import routing_checks as c, routing_input, routing_native, ses_checks
from autorouter import sexpr as sx, pipeline as p

ROOT=Path(__file__).resolve().parents[2]

class RoutingChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=ROOT/'evidence/pic-selective-area-observation-002'
        cls.retained=json.loads((src/'observations.json').read_text())
        cls.expected=json.loads((src/'expectations.json').read_text())
        cls.mixed=(src/'mixed.dsn').read_bytes()
        cls.source=(ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb').read_bytes()
        context=json.loads((ROOT/'evidence/pic-mixed-transport-probe-005/context.json').read_text())
        cls.unrouted,cls.removal=routing_input.derive(cls.mixed,cls.expected,cls.source,context)

    def synthetic(self):
        row=copy.deepcopy(self.retained['case'])
        ids={r['id'] for r in row['state']['items'] if r['kind'] not in c.ROUTE_KINDS}
        for key in ('state_before_local','state','state_after_selective'):
            state=row[key];state['items']=[r for r in state['items'] if r['id'] in ids]
            state['census'].update(items=len(ids),traces=0,vias=0)
            for section in ('items','pins','areas'):
                for r in state[section]:r['contacts']=[i for i in r['contacts'] if i in ids]
            for net in state['nets']:
                net['connected_sets']=[[i for i in group if i in ids] for group in net['connected_sets']]
        for key in ('route_geometry_before_local','route_geometry','route_geometry_after_selective'):
            row[key]={'trace_count':0,'via_count':0,'traces':[],'vias':[]}
        for key in ('predicates_before','predicates_after'):
            pred=row[key];pred.update(route_count=0,item_count=len(ids),trace_shape_count=0,trace_queries=[])
            pred['tree_entries']=[r for r in pred['tree_entries'] if r['id'] in ids]
            pred['indexed_items']=sum(r['valid'] for r in pred['tree_entries'])
            for a in pred['areas']:a['routes']=[]
        expected=dict(self.expected,derived_dsn_sha256=self.removal['unrouted_dsn_sha256'])
        row['input_sha256']=expected['derived_dsn_sha256']
        settings={'autorouter':{'enabled':False,'algorithm':'freerouting-router','max_passes':30},
            'optimizer':{'enabled':False},'fanout':{'enabled':False},'automatic_neckdown':False,'neck_width_um':0,
            'plane_as_obstacle':False,'plane_nets':[],'max_threads':1}
        def serial(v):return {'configuration_json':json.dumps(v),'layers_json':'[{"routable":true},{"routable":true}]','board_specific_costs_applied':True}
        loaded=serial(settings);settings['autorouter']['enabled']=True;enabled=serial(settings)
        result={'schema':1,'mode':'selective_route_diagnostic','status':'observed','routing_executed':True,'ses_executed':True,
            'cancel_before_routing':True,'case':row,'settings_loaded':loaded,'settings_enabled':enabled,'settings_final':copy.deepcopy(enabled),
            'routing':{'pipeline_invoked':True,'pipeline_returned':True,'uses_final_job_board':True,'cooperative_deadline_seconds':60,
                'cooperative_deadline_reached':False,'stop_requested':True,'wall_seconds':0.01,'board_object_replaced':False},
            'final_state':copy.deepcopy(row['state_after_selective']),'final_geometry':copy.deepcopy(row['route_geometry_after_selective']),
            'final_predicates':copy.deepcopy(row['predicates_after'])}
        result['writer']={'state_after_ses':copy.deepcopy(result['final_state']),'route_geometry_after_ses':copy.deepcopy(result['final_geometry'])}
        return result,expected

    def test_synthetic_cancel_is_only_lifecycle(self):
        value,expected=self.synthetic();result=c.compare(value,expected,self.retained)
        self.assertTrue(result['lifecycle_verified']);self.assertFalse(result['routing_accepted'])

    def test_original_rules_plane_geometry_and_settings_changes_reject(self):
        changes=[lambda r:r['final_state']['matrix'][0].update(raw_um=1),
            lambda r:next(a for a in r['final_state']['areas'] if a['nets']==['GND']).update(obstacle=True),
            lambda r:r['final_state']['pins'][0]['position_um'].__setitem__(0,0),
            lambda r:r['routing'].update(uses_final_job_board=False),
            lambda r:r['routing'].update(pipeline_returned=False),
            lambda r:r['routing'].update(stop_requested=False),
            lambda r:r['settings_final'].update(configuration_json='{}'),
            lambda r:r['case']['route_geometry']['vias'].append({'id':-1}),
            lambda r:r['final_predicates']['tree_entries'].pop(),
            lambda r:r['writer']['state_after_ses']['areas'][0].update(fixed='UNFIXED')]
        for mutate in changes:
            value,expected=self.synthetic();before=copy.deepcopy(value);mutate(value)
            self.assertNotEqual(value,before)
            with self.assertRaises((ValueError,KeyError)):c.compare(value,expected,self.retained)

    def test_effective_settings_and_lifecycle_falsifiers(self):
        for case in ('layers','duplicate','costs','time','schema'):
            value,expected=self.synthetic()
            if case=='layers':
                for phase in ('settings_loaded','settings_enabled','settings_final'):
                    value[phase]['layers_json']='[{"routable":false},{"routable":false}]'
            elif case=='duplicate':
                for phase in ('settings_loaded','settings_enabled','settings_final'):
                    value[phase]['configuration_json']=value[phase]['configuration_json'][:-1]+',"max_threads":1}'
            elif case=='costs':
                for phase in ('settings_loaded','settings_enabled','settings_final'):value[phase]['board_specific_costs_applied']='unobserved'
            elif case=='time':value['routing']['wall_seconds']=-1
            else:value['schema']=True
            with self.subTest(case=case),self.assertRaises(ValueError):c.compare(value,expected,self.retained)

    def test_shared_single_row_check_preserves_old_two_case_requirement(self):
        value,expected=self.synthetic();row=value['case']
        self.assertEqual(len(c.transport.validate_local_rows([row],expected,(False,))),1)
        with self.assertRaises(ValueError):c.transport.validate_local({'schema':1,'routing_executed':False,'ses_executed':False,'cases':[row]},expected)

    def test_generated_ses_requires_empty_seed_and_exact_engine_geometry(self):
        # Actual retained writer bytes serve only as a pure comparison fixture.
        src=ROOT/'evidence/pic-custom-ses-roundtrip-001';raw=(src/'raw.ses').read_bytes()
        geometry=json.loads((src/'observations.json').read_text())['cases'][1]['route_geometry']
        task=sx.parse(self.source.decode());task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
        _,result=ses_checks.audit(raw,self.unrouted,self.expected,task,geometry,generated=True)
        self.assertTrue(result['generated_engine_to_ses_exact']);self.assertFalse(result['exact_route_survival'])
        with self.assertRaises(ValueError):ses_checks.audit(raw,self.mixed,self.expected,task,geometry,generated=True)
        with self.assertRaises(ValueError):ses_checks.audit(raw,self.unrouted,self.expected,sx.parse(self.source.decode()),geometry,generated=True)
        changed=copy.deepcopy(geometry);changed['traces'][0]['corners_um'][0][0]+=1
        _,result=ses_checks.audit(raw,self.unrouted,self.expected,task,changed,generated=True)
        self.assertFalse(result['generated_engine_to_ses_exact'])

    def routing_positive(self):
     value,expected=self.synthetic();value['cancel_before_routing']=False;value['routing'].update(stop_requested=False,wall_seconds=0.2,board_object_replaced=False)
     old=self.retained['case'];route=copy.deepcopy(old['route_geometry_after_selective']['traces'][0]);rid=route['id']
     item=copy.deepcopy(next(r for r in old['state_after_selective']['items'] if r['id']==rid));item['contacts']=[];route['contacts']=[]
     state=value['final_state'];state['items'].append(item);state['census']['traces']=1;state['census']['items']+=1
     value['final_geometry']={'trace_count':1,'via_count':0,'traces':[route],'vias':[]}
     pred=value['final_predicates'];op=old['predicates_after'];pred['tree_entries'].append(copy.deepcopy(next(r for r in op['tree_entries'] if r['id']==rid)))
     pred['indexed_items']+=1;pred['route_count']=1;pred['item_count']+=1
     for a in pred['areas']:
      a['routes']=[copy.deepcopy(next(r for r in next(x for x in op['areas'] if x['id']==a['id'])['routes'] if r['id']==rid))]
     query=copy.deepcopy(next(r for r in op['trace_queries'] if r['id']==rid));ids={r['id'] for r in state['items']}
     for key in ('raw_overlap_ids','flag_filtered_overlap_ids'):query[key]=[i for i in query[key] if i in ids]
     pred['trace_queries']=[query];pred['trace_shape_count']=query['shape_count']
     value['writer']={'state_after_ses':copy.deepcopy(state),'route_geometry_after_ses':copy.deepcopy(value['final_geometry'])}
     return value,expected

    def layer_negative(self,v):
     r=v['final_geometry']['traces'][0];i=next(x for x in v['final_state']['items'] if x['id']==r['id'])
     r.update(layer_index=-1,first_layer=-1,last_layer=-1,layer='bottom_layer');i.update(first_layer=-1,last_layer=-1)
     for a in v['final_predicates']['areas']:a['routes'][0]['shares_layer']=False

    def wrong_class(self,v):
     r=v['final_geometry']['traces'][0];r['clearance_class_index']=0
     next(x for x in v['final_state']['items'] if x['id']==r['id'])['clearance_class_index']=0

    def test_generated_route_layer_and_clearance_falsifiers(self):
        value,expected=self.routing_positive();self.assertTrue(c.compare(value,expected,self.retained)['lifecycle_verified'])
        for mutate in (self.layer_negative,self.wrong_class):
            value,expected=self.routing_positive();mutate(value)
            value['writer']={'state_after_ses':copy.deepcopy(value['final_state']),'route_geometry_after_ses':copy.deepcopy(value['final_geometry'])}
            with self.assertRaises(ValueError):c.compare(value,expected,self.retained)

    def test_native_diagnostic_retains_strict_geometry_failure_and_static_guards(self):
        value,expected=self.routing_positive()
        value['final_geometry']['traces'][0]['corners_board_integer'][0]=None
        value['writer']['route_geometry_after_ses']=copy.deepcopy(value['final_geometry'])
        with self.assertRaisesRegex(ValueError,'exact integer engine point required'):
            c.compare(value,expected,self.retained)
        result=c.compare(value,expected,self.retained,native_diagnostic=True)
        self.assertFalse(result['geometry_verified']);self.assertFalse(result['routing_accepted'])
        self.wrong_class(value)
        value['writer']={'state_after_ses':copy.deepcopy(value['final_state']),'route_geometry_after_ses':copy.deepcopy(value['final_geometry'])}
        with self.assertRaisesRegex(ValueError,'clearance class'):
            c.compare(value,expected,self.retained,native_diagnostic=True)

    def test_saved_proposal_audit_never_claims_exact_engine_geometry(self):
        raw=(ROOT/'evidence/pic-custom-ses-roundtrip-001/raw.ses').read_bytes()
        task=sx.parse(self.source.decode());task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
        _,result=ses_checks.audit(raw,self.unrouted,self.expected,task,generated=True,proposal_only=True)
        self.assertTrue(result['safe_structure']);self.assertFalse(result['generated_engine_to_ses_exact'])
        self.assertNotIn('engine_to_ses',result)
        for kwargs in ({'proposal_only':True},{'generated':True},{'generated':True,'proposal_only':True,'geometry':{}}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                ses_checks.audit(raw,self.unrouted,self.expected,task,**kwargs)
        with self.assertRaisesRegex(ValueError,'empty seed'):
            ses_checks.audit(raw,self.mixed,self.expected,task,generated=True,proposal_only=True)
        with self.assertRaisesRegex(ValueError,'SES net'):
            ses_checks.audit(raw.replace(b'Net-(Q2-C)',b'unknown-net'),self.unrouted,self.expected,task,generated=True,proposal_only=True)

    def test_adapter_import_projection_keeps_rectangles_plane_and_other_rules_explicit(self):
        from experiments.pic_mixed_transport_probe_v1 import routing_adapter
        from decimal import Decimal
        context=json.loads((ROOT/'evidence/pic-mixed-transport-probe-005/context.json').read_text())
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as td:
            path=Path(td)/'input.dsn';path.write_bytes(self.unrouted);receipt=routing_adapter.apply(path,context)
        retained=self.retained['case']['state_after_selective'];state=copy.deepcopy(retained)
        plane=next(a for a in state['areas'] if a['nets']==['GND']);pid=plane['id']
        state['areas']=[a for a in state['areas'] if a['id']!=pid];state['census']['areas']-=1
        state['items']=[a for a in state['items'] if a['id']!=pid]
        next(n for n in state['nets'] if n['name']=='GND')['contains_plane']=False
        kind='app.freerouting.board.model.items.ObstacleArea'
        state['adapter_obstacles']=[copy.deepcopy(i) for i in state['items'] if i['kind']==kind]
        transforms=[r for r in receipt['adapter']['transformations'] if r['kind']=='native_graphic_bbox_keepout']
        for index,rect in enumerate(transforms):
            layer=state['layers'].index(rect['dsn_layer']);x0,y0,x1,y1=map(Decimal,rect['rect_um'])
            item={'id':30000+index,'kind':kind,'nets':[],'fixed':'SYSTEM_FIXED','clearance_class_index':1,'first_layer':layer,'last_layer':layer,'contacts':[]}
            state['items'].append(item)
            ring=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
            state['adapter_obstacles'].append(dict(copy.deepcopy(item),layer=rect['dsn_layer'],layer_index=layer,holes=0,hole_shapes=[],ring_unavailable=False,corner_count=4,border_class='app.freerouting.geometry.planar.IntBox',ring_classes=['app.freerouting.geometry.planar.IntPoint']*4,ring_um=[[float(x) for x in point] for point in ring],ring_board_integer=[[int(x*10) for x in point] for point in ring]))
        state['adapter_obstacle_count']=33
        self.assertEqual(len(c.adapter_projection(state,retained,receipt)),19)
        for case in ('shrink','omission','plane','clearance','width','bowtie','opposite_layer','unavailable'):
            bad=copy.deepcopy(state)
            if case=='shrink':bad['adapter_obstacles'][-1]['ring_um'][0][0]+=0.1
            elif case=='omission':bad['adapter_obstacles'].pop()
            elif case=='plane':next(n for n in bad['nets'] if n['name']=='GND')['contains_plane']=True
            elif case=='clearance':bad['adapter_obstacles'][-1]['clearance_class_index']=0
            elif case=='width':bad['nets'][0]['width_um'][0]+=1
            elif case=='bowtie':
                for field in ('ring_um','ring_board_integer'):
                    ring=bad['adapter_obstacles'][-1][field];ring[1],ring[2]=ring[2],ring[1]
            elif case=='opposite_layer':
                row=bad['adapter_obstacles'][-1];other=1-row['layer_index'];row.update(layer_index=other,first_layer=other,last_layer=other)
                next(item for item in bad['items'] if item['id']==row['id']).update(first_layer=other,last_layer=other)
            else:bad['adapter_obstacles'][-1].update(ring_unavailable=True,border_class='app.freerouting.geometry.planar.Circle',corner_count=0)
            with self.subTest(case=case),self.assertRaises(ValueError):c.adapter_projection(bad,retained,receipt)

    def test_native_task_copy_retains_original_intent_and_rules(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as td:
            target=routing_native.task_copy(ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb',Path(td)/'task')
            self.assertEqual(p.routes(sx.read(target)),[])
            self.assertEqual(p.immutable(sx.read(target)),p.immutable(sx.parse(self.source.decode())))

    def test_refill_working_candidate_seals_without_unfreezing_prior_evidence(self):
        from experiments.pic_mixed_transport_probe_v1 import driver
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as td:
            out=Path(td);target=out/'routing-native/candidate'/driver.original.SOURCE.name
            target.parent.mkdir(parents=True);old=out/'completed.json';old.write_text('{}')
            frozen={'completed.json':p.sha(old)};mutable=set()
            def capture():
                for path in (old,target):
                    key=str(path.relative_to(out))
                    if path.exists() and key not in mutable:
                        digest=p.sha(path)
                        if key in frozen and frozen[key]!=digest:raise ValueError('prior evidence changed')
                        frozen[key]=digest
            with driver.pending_candidate(out,target,frozen,mutable,capture):
                target.write_text('before fill');capture();target.write_text('after fill');capture()
            self.assertEqual(frozen[str(target.relative_to(out))],p.sha(target));self.assertFalse(mutable)
            with self.assertRaises(ValueError),driver.pending_candidate(out,target,frozen,mutable,capture):pass
            with self.assertRaises(ValueError),driver.pending_candidate(out,old,frozen,mutable,capture):pass
            old.write_text('tampered')
            with self.assertRaises(ValueError):capture()

    def test_failed_refill_seals_failed_candidate(self):
        from experiments.pic_mixed_transport_probe_v1 import driver
        with tempfile.TemporaryDirectory(dir=ROOT/'.runs') as td:
            out=Path(td);target=out/'routing-native/candidate'/driver.original.SOURCE.name
            target.parent.mkdir(parents=True);frozen={};mutable=set()
            def capture():frozen[str(target.relative_to(out))]=p.sha(target)
            with self.assertRaises(RuntimeError),driver.pending_candidate(out,target,frozen,mutable,capture):
                target.write_text('failed partial output');raise RuntimeError('native failure')
            self.assertFalse(mutable);self.assertEqual(frozen[str(target.relative_to(out))],p.sha(target))

if __name__=='__main__':unittest.main()
