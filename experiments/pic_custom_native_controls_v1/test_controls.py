"""Pure falsifiers only. Synthetic observations are never native evidence."""
import ast,copy,json,os,shutil,signal,sys,tempfile,unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock
import driver as d
import fixture as fx
import checks
import recipes as g
from autorouter.adapter import _dump_dsn,_QUOTE_SENTINEL

def model(scene,project):
    """Explicit synthetic observer/DSN model, used only to test control guards."""
    layer=scene['copper_layer'];back=scene['variant']=='back90';angle=90 if back else 0
    codes={'CONTACT':1,'FOREIGN':2};pads=[];fps=[];terms=[];custom=[];images=[];stacks=[];placed=[]
    for item in scene['pads']:
        pad={'uuid':item['uuid'],'reference':item['reference'],'number':'1','net':item['net'],'netcode':codes[item['net']],'copper_layers':[layer],'position_nm':list(item['at'])};pads.append(pad)
        terms.append({**pad,'footprint_uuid':item['footprint_uuid'],'fp_relative_position_nm':[0,0],'orientation_degrees':angle,'flipped':back})
        fps.append({'uuid':item['footprint_uuid'],'reference':item['reference'],'position_nm':list(item['at']),'orientation_degrees':angle,'layer':layer,'flipped':back})
        stack=item['id']+'_stack';images.append(['image',item['id'],['pin',stack,'1','0','0']])
        placed.append(['component',item['id'],['place',item['reference'],str(Decimal(item['at'][0])/1000),str(-Decimal(item['at'][1])/1000),'back' if back else 'front','270' if back else '0',['PN','Owned_'+item['reference']]]])
        if 'polygon' not in item:
            stacks.append(['padstack',stack,['shape',['circle','top_layer','1500']]]);continue
        source=g.CONVEX if item['id']=='CONVEX' else g.CONCAVE
        local=[(x,-y if back else y) for x,y in source]
        def shape(points):return {'arc_count':0,'outlines':[{'outline':{'closed':True,'points_nm':[list(p) for p in points]},'holes':[]}],'total_vertices':len(points)}
        custom.append({**pad,'footprint_uuid':item['footprint_uuid'],'fp_relative_position_nm':[0,0],'orientation_degrees':angle,'pad_flipped':back,
            'footprint_position_nm':list(item['at']),'footprint_orientation_degrees':angle,'footprint_flipped':back,
            'shape':'custom','anchor':'rect','attribute':'smd','size_nm':[300000,300000],'offset_nm':[0,0],'drill_nm':[0,0],
            'merged_local':shape(local),'transformed_world':shape(item['polygon']),'effective_world':shape(item['polygon'])})
        ring=g.hull(tuple((x,-y) for x,y in source));ring=ring+ring[:1]
        stacks.append(['padstack',stack,['shape',['polygon','top_layer','0',*[str(Decimal(v)/1000) for pt in ring for v in pt]]]])
    native={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':'export','board_saved':False,'routing_accepted':False,'pads':pads,
        'routes':[{'uuid':row['uuid'],'net':row['net'],'kind':'segment','width_nm':500000,'start_nm':list(row['start']),'end_nm':list(row['end']),'layer':layer} for row in scene['tracks']],
        'nets':[{'name':name,'netcode':code,'class':'Default','copper_pad_count':2,'width_nm':500000,'clearance_nm':250000,'via_diameter_nm':1600000,'via_drill_nm':600000} for name,code in codes.items()],
        'floors_nm':{k:int(Decimal(str(project['board']['design_settings']['rules'][k]))*1000000) for k in checks.g.FLOORS},'obstacles':[]}
    state={'schema':1,'total_pad_count':4,'all_footprints':fps,'all_terminals':terms,'pads':custom,'routing_accepted':False,'geometry_qualified':False}
    extra={'same_loaded_board':True,'board_saved':False,'geometry_qualified':False,'routing_accepted':False,'observation_before_export':state,'observation_after_export':copy.deepcopy(state)}
    network=['network',*[['net',name,['pins',*[item['reference']+'-1' for item in scene['pads'] if item['net']==name]]] for name in codes]]
    raw=_dump_dsn(['pcb','synthetic',['parser',['string_quote',_QUOTE_SENTINEL]],['unit','um'],['resolution','um','10'],['library',*images,*stacks],['placement',*placed],network]).encode()
    return native,extra,raw

def native_report(case,scene,ignored):
    pads={row['id']:row['uuid'] for row in scene['pads']};tracks={row['id']:row['uuid'] for row in scene['tracks']}
    raw={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':d.SOURCE.name,'included_severities':['error','warning','exclusion'],
        'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[{'key':key} for key in ignored]}
    if case=='false_hull':raw['unconnected_items']=[{'type':'unconnected_items','severity':'error','items':[{'uuid':pads['CONCAVE']},{'uuid':tracks['CONTACT_TRACK']}]}]
    if case=='foreign_intrusion':raw['violations']=[{'type':'clearance','severity':'error','items':[{'uuid':pads['CONCAVE']},{'uuid':tracks['FOREIGN_TRACK']}]}]
    return raw

def summary(raw):
    findings=raw['violations']+raw['unconnected_items']+raw['schematic_parity']
    return {'opens':len(raw['unconnected_items']),'blocking':sum(r['severity']=='error' for r in raw['violations']+raw['schematic_parity']),
        'warnings':sum(r['severity']=='warning' for r in findings),'exclusions':sum(r['severity']=='exclusion' or r.get('excluded',False) for r in findings),'ignored_checks':raw['ignored_checks'],'findings':findings}

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=d.sx.read(d.SOURCE);cls.project=d.read(d.SOURCE.with_suffix('.kicad_pro'));cls.hashes,cls.total=d.source_binding()
        cls.ignored=list(d.OBSERVED_IGNORED)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=d.HERE,prefix='pure-');self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)
    def scene(self,case='positive',variant='front0'):return fx.prepare(self.original,case,variant)[1]
    def test_fixture_exact_single_endpoint_changes_only(self):
        for variant in fx.VARIANTS:
            positive,_=fx.prepare(self.original,'positive',variant);tree=d.sx.parse(positive.decode())
            self.assertEqual(len(d.p.routes(tree)),2);self.assertEqual(len(d.sx.children(tree,'footprint')),4)
            self.assertEqual(d.sx.one(tree,'setup'),d.sx.one(self.original,'setup'))
            for case,index in [('false_hull',0),('foreign_intrusion',1)]:
                changed,_=fx.prepare(self.original,case,variant);other=d.sx.parse(changed.decode());expected=copy.deepcopy(tree)
                d.sx.one(d.p.routes(expected)[index],'end')[:]=d.sx.one(d.p.routes(other)[index],'end')
                self.assertEqual(expected,other)
    def test_all_six_synthetic_exact_geometry_and_predicates(self):
        for variant,case in fx.ORDER:
            scene=self.scene(case,variant);n,custom,raw=model(scene,self.project)
            result=checks.observe(n,custom,raw,scene,self.project);self.assertTrue(result['geometry_matches_fixed_recipe']);self.assertFalse(result['custom_routing_support_qualified'])
            report=native_report(case,scene,self.ignored);self.assertTrue(checks.predicate(case,summary(report),report,scene,self.ignored)[0])
    def test_actual_original_still_blocked_and_unused_class_retained(self):
        self.assertEqual({row['name'] for row in self.project['net_settings']['classes']},{'Default','POWER'})
        with self.assertRaises(d.p.Rejected) as cm:d.p.preflight(d.SOURCE)
        self.assertEqual(str(cm.exception),d.EXPECTED_GATE)
        self.assertEqual((len(self.hashes),self.total),(15,1366598))
    def test_fixed_back90_requires_native_angles_and_world_geometry(self):
        for field,value in [('orientation_degrees',0),('flipped',False),('flipped',1)]:
            scene=self.scene(variant='back90');n,c,raw=model(scene,self.project)
            for which in ('observation_before_export','observation_after_export'):c[which]['all_footprints'][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):checks.observe(n,c,raw,scene,self.project)
    def test_hull_substitution_cannot_pass_native_copper_observation(self):
        scene=self.scene();n,c,raw=model(scene,self.project)
        for which in ('observation_before_export','observation_after_export'):
            row=next(r for r in c[which]['pads'] if r['reference']=='CONCAVE')
            shape=row['effective_world'];points=g.hull(tuple(map(tuple,shape['outlines'][0]['outline']['points_nm'])))
            shape['outlines'][0]['outline']['points_nm']=list(map(list,points));shape['total_vertices']=len(points)
        with self.assertRaisesRegex(ValueError,'world copper'):checks.observe(n,c,raw,scene,self.project)
    def test_default_width_and_original_floor_tamper_rejects(self):
        for variant in ('width','floor'):
            scene=self.scene();n,c,raw=model(scene,self.project)
            if variant=='width':n['nets'][0]['width_nm']=200000
            else:n['floors_nm']['min_clearance']+=1
            with self.subTest(variant=variant),self.assertRaises(ValueError):checks.observe(n,c,raw,scene,self.project)
    def test_export_flip_restoration_and_wrong_layer_rejects(self):
        scene=self.scene();n,c,raw=model(scene,self.project);c['observation_after_export']['all_terminals'][0]['net']='wrong'
        with self.assertRaisesRegex(ValueError,'restore'):checks.observe(n,c,raw,scene,self.project)
        n,c,raw=model(scene,self.project);n['pads'][0]['copper_layers']=['B.Cu']
        with self.assertRaisesRegex(ValueError,'terminal'):checks.observe(n,c,raw,scene,self.project)
    def test_dsn_wrong_quote_hull_or_side_rejects(self):
        for variant in ('quote','side','hull'):
            scene=self.scene(variant='back90');n,c,raw=model(scene,self.project)
            if variant=='quote':bad=raw.replace(b'(string_quote ")',b'')
            elif variant=='side':bad=raw.replace(b'back 270',b'front 270',1)
            else:bad=raw.replace(b'-650',b'-600',1)
            self.assertNotEqual(bad,raw)
            with self.subTest(variant=variant),self.assertRaises(ValueError):checks.observe(n,c,bad,scene,self.project)
    def test_false_contact_requires_raw_unconnected_target_not_violation(self):
        scene=self.scene('false_hull');raw=native_report('false_hull',scene,self.ignored);row=raw['unconnected_items'].pop();raw['violations'].append(row)
        self.assertFalse(checks.predicate('false_hull',summary(raw),raw,scene,self.ignored)[0])
    def test_false_contact_unrelated_or_excluded_open_never_qualifies(self):
        for variant in ('wrong_target','extra_open','excluded','warning','none'):
            scene=self.scene('false_hull');raw=native_report('false_hull',scene,self.ignored)
            if variant=='wrong_target':raw['unconnected_items'][0]['items'][0]['uuid']='unrelated'
            if variant=='extra_open':raw['unconnected_items'].append({'type':'unconnected_items','severity':'error','items':[{'uuid':'wrong'}]})
            if variant=='excluded':raw['unconnected_items'][0]['excluded']=True
            if variant=='warning':raw['unconnected_items'][0]['severity']='warning'
            if variant=='none':raw['unconnected_items']=[]
            with self.subTest(variant=variant):self.assertFalse(checks.predicate('false_hull',summary(raw),raw,scene,self.ignored)[0])
    def test_intrusion_track_only_error_or_open_never_qualifies(self):
        for variant in ('track_only','open','unrelated_error'):
            scene=self.scene('foreign_intrusion');raw=native_report('foreign_intrusion',scene,self.ignored)
            if variant=='track_only':raw['violations'][0]['items'][0]['uuid']=scene['tracks'][0]['uuid']
            if variant=='open':raw['unconnected_items']=[{'type':'unconnected_items','severity':'error','items':[]}]
            if variant=='unrelated_error':raw['violations'].append({'type':'shorting_items','severity':'error','items':[{'uuid':'other'}]})
            with self.subTest(variant=variant):self.assertFalse(checks.predicate('foreign_intrusion',summary(raw),raw,scene,self.ignored)[0])
    def test_critical_warning_ignored_setting_exclusion_rejects(self):
        for variant in ('critical','ignored','exclusion'):
            scene=self.scene();raw=native_report('positive',scene,self.ignored)
            if variant=='critical':raw['violations']=[{'type':'padstack_invalid','severity':'warning','items':[]}]
            if variant=='ignored':raw['ignored_checks'].append({'key':'clearance'})
            if variant=='exclusion':raw['violations']=[{'type':'clearance','severity':'exclusion','items':[]}]
            with self.subTest(variant=variant):self.assertFalse(checks.predicate('positive',summary(raw),raw,scene,self.ignored)[0])
    def test_unknown_warning_or_unqualified_new_provider_rejects_all_cases(self):
        for case in fx.CASES:
            scene=self.scene(case)
            for kind in ('unknown_provider','missing_tuning_profile','footprint_symbol_field_mismatch','text_on_edge_cuts','track_on_post_machined_layer'):
                raw=native_report(case,scene,self.ignored);raw['violations'].append({'type':kind,'severity':'warning','items':[]})
                with self.subTest(case=case,kind=kind):self.assertFalse(checks.predicate(case,summary(raw),raw,scene,self.ignored)[0])
            raw=native_report(case,scene,self.ignored);raw['violations'].append({'type':'lib_footprint_issues','severity':'warning','items':[]})
            self.assertTrue(checks.predicate(case,summary(raw),raw,scene,self.ignored)[0])
    def test_effective_ignored_set_missing_duplicate_unexpected_rejects(self):
        explicit=sorted(k for k,v in self.project['board']['design_settings']['rule_severities'].items() if v=='ignore')
        self.assertEqual(set(self.ignored)-set(explicit),{'track_not_centered_on_via'})
        self.assertEqual(d.digest(d.ROOT/d.BASELINE_REPORT_REL),d.BASELINE_REPORT_SHA)
        for keys in (explicit,self.ignored+[self.ignored[0]],self.ignored+['clearance'],['wrong']):
            scene=self.scene();raw=native_report('positive',scene,keys)
            self.assertFalse(checks.predicate('positive',summary(raw),raw,scene,self.ignored)[0])
    def record(self):return {'status':'controls_passed','controls_passed':True,**d.FALSE_CLAIMS}
    def test_publisher_positive_and_final_material_changes(self):
        for variant in ('positive','canonical','return','cap','cancel','stale'):
            out=self.out/variant;out.mkdir();record=self.record();expired=[]
            def scan(_):
                if variant=='canonical':r=d.read(out/'summary.json');r['geometry_qualified']=True;d.p.save_json(out/'summary.json',r)
                if variant=='return':record['geometry_qualified']=True
                if variant=='cap':expired.append(1)
                return 0
            calls=[]
            def stable():
                calls.append(1)
                if len(calls)==2:
                    if variant=='cancel':raise KeyboardInterrupt
                    if variant=='stale':raise ValueError('changed file')
            with mock.patch.object(d,'size',side_effect=scan):r=d.publish(out,record,stable,lambda:None,lambda:0 if expired else 1)
            self.assertIs(r['controls_passed'],variant=='positive');self.assertIs(d.read(out/'summary.json')['controls_passed'],variant=='positive')
            self.assertFalse(r['geometry_qualified'])
    def test_failed_rewrite_leaves_no_ready_canonical(self):
        save=d.p.save_json;calls=[]
        def writer(path,row):
            calls.append(1)
            if len(calls)>1:raise OSError('correction failure')
            save(path,row)
        with mock.patch.object(d.p,'save_json',side_effect=writer):r=d.publish(self.out,self.record(),mock.Mock(side_effect=[None,KeyboardInterrupt]),lambda:None,lambda:1)
        self.assertFalse(r['controls_passed']);self.assertFalse((self.out/'summary.json').exists());self.assertTrue(list(self.out.glob('invalidated-*')))
    def test_scoped_real_self_signals_restore(self):
        root=self.out/'root';(root/'.runs').mkdir(parents=True)
        for sig in (signal.SIGINT,signal.SIGTERM):
            old={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
            def execute(*a,**k):return d.publish(root/'.runs',self.record(),lambda:os.kill(os.getpid(),sig),lambda:None,lambda:1)
            with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'experiment',side_effect=execute),mock.patch('builtins.print'):
                self.assertEqual(d.main(['--output',str(root/'.runs/out'),'--run-native']),2)
            self.assertEqual(old,{s:signal.getsignal(s) for s in old})
    def test_stage_freeze_precedes_parser_and_commands_reject_save_engine(self):
        job=object.__new__(d.ControlJob);job.out=self.out;job.batch=self.out;job.remaining=lambda:100;job.env={};job.steps=[];job.stage_evidence={}
        def run(argv,**kwargs):
            for name in ('observation.json','custom-pads.json','native.dsn','observe.log'):(self.out/name).write_bytes(b'first')
            return {'status':'success','exit_code':0,'cleanup_complete':True}
        with mock.patch.object(d,'run',side_effect=run):job.step('observe',d.observe_argv(self.out),already_sandboxed=True)
        (self.out/'custom-pads.json').write_bytes(b'stale');self.assertNotEqual(job.stage_evidence['observe']['custom-pads.json'],d.digest(self.out/'custom-pads.json'))
        with mock.patch.object(d,'run') as runner:
            for name,argv in [('engine',['java']),('original-drc',d.drc_argv(self.out)+['--save-board'])]:
                with self.assertRaises(d.p.Rejected):job.step(name,argv,already_sandboxed=True)
        runner.assert_not_called()
    def test_budget_before_worker_and_snapshot_mismatch(self):
        job=object.__new__(d.ControlJob);job.out=self.out;job.batch=self.out;job.remaining=lambda:0
        with mock.patch.object(d,'run') as run:
            with self.assertRaises(d.p.Rejected):job.step('observe',d.observe_argv(self.out),already_sandboxed=True)
        run.assert_not_called()
        with mock.patch.object(d.subprocess,'run',return_value=type('R',(),{'stdout':b'changed'})()):
            with self.assertRaisesRegex(d.p.Rejected,'commit exact'):d.snapshot(self.out,{'git_head':'mock','implementation_sha256':{}})
    def test_worker_only_changes_census_from_qualified_getters(self):
        source=(d.ROOT/'experiments/pic_custom_observer_v1/worker.py').read_text()
        expected=source.replace('nonsaving custom-pad observation callback','nonsaving owned custom-pad control callback').replace("'pads':512,'footprints':128,'custom_pads':8", "'pads':4,'footprints':4,'custom_pads':2").replace('len(footprints)!=63','len(footprints)!=4').replace('count!=247','count!=4').replace('pinned original custom-pad census differs','owned fixed custom-pad census differs')
        self.assertEqual((d.HERE/'worker.py').read_text(),expected)
    def test_complete_mocked_flow_and_real_file_stage_final_falsifiers(self):
        for variant in ('unchanged','positive_failed','wrong_world','parsed_observation','parsed_drc','parsed_binding','late_case','late_source','late_helper','late_tool'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory(dir=self.out,prefix=variant+'-') as tmp:
                root=Path(tmp);(root/'.runs').mkdir();source=root/'source';shutil.copytree(d.SOURCE.parent,source);board=source/d.SOURCE.name
                baseline=root/d.BASELINE_REPORT_REL;baseline.parent.mkdir(parents=True);shutil.copyfile(d.ROOT/d.BASELINE_REPORT_REL,baseline)
                receipt=root/'manifest.json';receipt.write_text('{}');helper=root/'helper.py';helper.write_text('# synthetic helper\n');tool=root/'tool';tool.write_text('synthetic tool, never executed')
                wrapper=root/'wrapper.py';wrapper.write_text('# synthetic wrapper\n');out=root/'.runs/batch';mutated=[];calls=[]
                hashes=d.inventory(source);total=sum((source/name).stat().st_size for name in hashes)
                tools={'git_head':'synthetic','implementation_sha256':{},'files':{str(tool):d.digest(tool)}};original_read=d.read;original_parse=d.p.parse_report
                def snapshot(out,tools,remaining):
                    (out/'code').mkdir();shutil.copyfile(helper,out/'code/helper.py');return {'helper.py':d.digest(helper)}
                def manifest():
                    if variant in ('late_source','late_helper','late_tool') and (out/'summary.json').exists() and not mutated:
                        path={'late_source':board.with_suffix('.kicad_pro'),'late_helper':helper,'late_tool':tool}[variant];path.write_bytes(path.read_bytes()+b'\n');mutated.append(variant)
                    return tools
                def read(path):
                    value=original_read(path)
                    if variant=='parsed_observation' and Path(path).name=='observation.json' and not mutated:
                        changed=copy.deepcopy(value);changed['floors_nm']['min_clearance']+=1;d.p.save_json(Path(path),changed);mutated.append(variant)
                    return value
                def parse(path,name):
                    value=original_parse(path,name)
                    if variant in ('parsed_drc','parsed_binding') and not mutated:
                        target=Path(path) if variant=='parsed_drc' else Path(path).with_name('original-drc-binding.json')
                        changed=original_read(target);changed['injected_after_parse']=True;d.p.save_json(target,changed);mutated.append(variant)
                    return value
                def run(argv,**kwargs):
                    directory=kwargs['cwd'];name=kwargs['log'].stem;v,c=directory.name.split('-',1);scene=fx.prepare(self.original,c,v)[1]
                    kwargs['log'].write_text('mock native stage; no process launched\n');calls.append((v,c,name));exit_code=0
                    if name=='observe':
                        n,custom,raw=model(scene,self.project);input_board=directory/'observe-input'/board.name;tree=d.inventory(input_board.parent)
                        n.update(source=str(input_board),board_sha256=tree[board.name],project_sha256=tree[board.with_suffix('.kicad_pro').name],input_hashes_before=tree,input_hashes_after=tree,dsn_sha256=d.sha_bytes(raw),limits=d.f.LIMITS)
                        if variant=='wrong_world' and not mutated:
                            for which in ('observation_before_export','observation_after_export'):custom[which]['pads'][0]['effective_world']['outlines'][0]['outline']['points_nm'][0][0]+=1
                            mutated.append(variant)
                        for key in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after'):custom[key]=n[key]
                        d.p.save_json(directory/'observation.json',n);custom['floor_context_sha256']=d.digest(directory/'observation.json');d.p.save_json(directory/'custom-pads.json',custom);(directory/'native.dsn').write_bytes(raw)
                        if variant=='late_case' and c=='false_hull' and v=='front0' and not mutated:
                            target=out/'front0-positive/observe-input'/board.with_suffix('.kicad_pro').name;target.write_bytes(target.read_bytes()+b'\n');mutated.append(variant)
                    else:
                        raw=native_report(c,scene,self.ignored)
                        if variant=='positive_failed' and c=='positive' and v=='front0':raw['violations']=[{'type':'clearance','severity':'error','items':[{'uuid':'unrelated'}]}];mutated.append(variant)
                        d.p.save_json(directory/'original-drc.json',raw);exit_code=5 if summary(raw)['findings'] else 0
                    return {'status':'nonzero_exit' if exit_code else 'success','exit_code':exit_code,'cleanup_complete':True,'argv':argv,'cwd':str(directory),'cpu_seconds':0,'monitor_cpu_seconds':0}
                with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'SOURCE',board),mock.patch.object(d,'RECEIPT',receipt),mock.patch.object(d,'RECEIPT_SHA',d.digest(receipt)),mock.patch.object(d,'WRAPPER',wrapper),mock.patch.object(d,'WRAPPER_SHA',d.digest(wrapper)),mock.patch.object(d,'source_binding',return_value=(hashes,total)),mock.patch.object(d,'snapshot',side_effect=snapshot),mock.patch.object(d.p,'tool_manifest',side_effect=manifest),mock.patch.object(d.p,'check_storage'),mock.patch.object(d,'run',side_effect=run),mock.patch.object(d,'read',side_effect=read),mock.patch.object(d.p,'parse_report',side_effect=parse):
                    result=d.experiment(out,run_native=True)
                saved=original_read(out/'summary.json')
                self.assertIs(result['controls_passed'],variant=='unchanged',result);self.assertEqual(saved,result);self.assertEqual(len(result['cases']),6)
                self.assertFalse(result['custom_routing_support_qualified']);self.assertFalse(result['geometry_qualified'])
                if variant=='unchanged':self.assertEqual(len(calls),12);self.assertEqual(d.inventory(source),hashes)
                else:self.assertTrue(mutated,variant)
                if variant=='positive_failed':
                    negatives=[row for row in result['cases'] if row['variant']=='front0' and row['case']!='positive']
                    self.assertTrue(all(row['expected_predicate_met'] for row in negatives));self.assertTrue(all(row['control_passed'] is False for row in negatives))
                if variant=='wrong_world':self.assertNotIn(('front0','positive','original-drc'),calls)

if __name__=='__main__':unittest.main()
