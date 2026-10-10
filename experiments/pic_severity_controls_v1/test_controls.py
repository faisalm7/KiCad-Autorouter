"""Pure/mock-native tests; zero native/engine jobs and no correctness claim."""
import copy,json,os,signal,shutil,tempfile,unittest
from pathlib import Path
from unittest import mock
import driver as d,fixture as fx,checks,intent

def model(scene,project):
    result={'schema':1,'native_version':'10.0.0','units':'integer nanometres','same_loaded_board':True,
        'board_saved':False,'dsn_exported':False,'routing_accepted':False,'schematic_parity_qualified':False,
        'floors_nm':{key:checks.nm(project['board']['design_settings']['rules'][key]) for key in ('min_track_width','min_clearance','min_via_diameter','min_through_hole_diameter','min_via_annular_width')},
        'pads':[],'footprints':[],'routes':scene['tracks'],'texts':[], 'nets':[]}
    layer_ids={'Dwgs.User':17,'F.Fab':35,'Edge.Cuts':25}
    for row in scene['texts']:
        result['texts'].append({**row,'layer_id':layer_ids[row['layer']],'layer':'User.Drawings' if row['layer']=='Dwgs.User' else row['layer']})
    for row in scene['pads']:
        pad={k:v for k,v in row.items() if k!='post_machined'}
        pad.update(size_nm=[3000000,3000000],drill_nm=[600000,600000],layers=['F.Cu','B.Cu'],post_machining={})
        for side in ('front','back'):
            active=row['post_machined'] and side=='front'
            pad['post_machining'][side]={'mode':'COUNTERBORE' if active else 'NOT_POST_MACHINED','mode_value':2 if active else 1,'size_nm':1200000 if active else 0,'depth_nm':200000 if active else 0,'angle_decidegrees':0}
        pad['affected_layers']=['F.Cu'] if row['post_machined'] else []
        result['pads'].append(pad);result['footprints'].append({'uuid':row['footprint_uuid'],'reference':row['reference'],'position_nm':row['position_nm'],'layer':'F.Cu'})
    classes={r['name']:r for r in project['net_settings']['classes']}
    for code,(name,clsname) in enumerate((('GND','POWER'),('SIGNAL_A','Default')),1):
        cls=classes[clsname];profile=cls['tuning_profile'] or classes['Default']['tuning_profile']
        effective='POWER,Default' if scene['case']=='missing_default_profile' and name=='GND' else clsname
        result['nets'].append({'name':name,'netcode':code,'class':effective,'width_nm':checks.nm(cls['track_width']),'clearance_nm':checks.nm(cls['clearance']),
            'via_diameter_nm':checks.nm(cls['via_diameter']),'via_drill_nm':checks.nm(cls['via_drill']),'tuning_profile':profile,'has_tuning_profile':bool(profile)})
    return result

def raw_report(case,scene,ignored):
    raw={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':d.SOURCE.name,
        'included_severities':['error','warning','exclusion'],'violations':[],'unconnected_items':[],'schematic_parity':[],
        'ignored_checks':[{'key':x} for x in ignored]}
    if case=='missing_named_profile':raw['violations']=[{'type':'missing_tuning_profile','severity':'warning','description':'Missing tuning profile (Net Class: POWER, Tuning Profile: MissingOwnedProfile)','items':[]}]
    if case in ('board_edge_text','footprint_edge_text'):raw['violations']=[{'type':'text_on_edge_cuts','severity':'error','items':[{'uuid':fx.uid('boardtext' if case=='board_edge_text' else 'fptext')}]}]
    if case=='pad_front_counterbore':raw['violations']=[{'type':'track_on_post_machined_layer','severity':'error','items':[{'uuid':fx.uid('pad2')},{'uuid':fx.uid('trackSIGNAL_A')}]}]
    return raw

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=d.sx.read(d.SOURCE);cls.project=d.read(d.SOURCE.with_suffix('.kicad_pro'));cls.hashes,cls.total=d.source_binding();cls.ignored=list(d.OBSERVED_IGNORED)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=d.HERE,prefix='pure-');self.addCleanup(self.tmp.cleanup);self.out=Path(self.tmp.name)
    def prepare(self,case):return fx.prepare(self.original,self.project,case)
    def test_exact_fixed_geometry_delta_and_project_profiles(self):
        raw,base,scene=self.prepare('positive');tree=d.sx.parse(raw.decode())
        self.assertEqual(base,self.project);self.assertEqual(len(d.p.routes(tree)),2)
        for case in fx.CASES:
            board,project,scene=self.prepare(case);other=d.sx.parse(board.decode());expected=copy.deepcopy(tree)
            delta=fx.project_delta(self.project,project,case)
            if case=='board_edge_text':d.sx.one(d.sx.one(expected,'gr_text'),'layer')[1]='"Edge.Cuts"'
            if case=='footprint_edge_text':d.sx.one(d.sx.one(d.sx.children(expected,'footprint')[0],'fp_text'),'layer')[1]='"Edge.Cuts"'
            if case=='pad_front_counterbore':d.sx.one(d.sx.children(expected,'footprint')[2],'pad').append(['front_post_machining','counterbore',['size','1.2'],['depth','0.2']])
            self.assertEqual(expected,other)
            self.assertEqual(project['board'],self.project['board'])
            self.assertEqual(bool(delta),case.startswith('missing_'))
            self.assertEqual(d.sx.one(other,'setup'),d.sx.one(self.original,'setup'))
    def test_guard_rejects_each_negative_and_original_has_no_intent(self):
        self.assertTrue(intent.audit(self.original,self.project)['source_intent_allowed'])
        for case in fx.CASES:
            raw,project,_=self.prepare(case);guard=intent.audit(d.sx.parse(raw.decode()),project)
            self.assertIs(guard['source_intent_allowed'],case=='positive')
            self.assertFalse(guard['production_support_changed'])
    def test_generic_guard_renaming_nesting_and_malformed_profiles(self):
        board,project,_=self.prepare('positive');tree=d.sx.parse(board.decode())
        project['net_settings']['classes'][1]['name']='Renamed';project['net_settings']['classes'][1]['tuning_profile']='Other'
        self.assertFalse(intent.audit(tree,project)['source_intent_allowed'])
        for token in intent.MACHINING|{'generated'}:
            value=copy.deepcopy(tree);d.sx.children(value,'footprint')[0].append([token])
            self.assertFalse(intent.audit(value,self.project)['source_intent_allowed'])
        for bad in (None,42,[]):
            value=copy.deepcopy(self.project);value['net_settings']['classes'][0]['tuning_profile']=bad
            with self.assertRaises(ValueError):intent.audit(tree,value)
        value=copy.deepcopy(self.project);value['tuning_profiles']['new_unknown_schema']=[]
        with self.assertRaises(ValueError):intent.audit(tree,value)
        value=copy.deepcopy(tree);value.append(['dimension',['layer','Edge.Cuts']]);self.assertFalse(intent.audit(value,self.project)['source_intent_allowed'])
    def test_stackup_allowed_but_duplicate_item_layer_and_edge_multilayer_reject(self):
        raw,project,_=self.prepare('positive');tree=d.sx.parse(raw.decode())
        self.assertTrue(d.sx.children(d.sx.one(d.sx.one(tree,'setup'),'stackup'),'layer'))
        self.assertTrue(intent.audit(tree,project)['source_intent_allowed'])
        wrong=copy.deepcopy(tree);d.sx.one(wrong,'gr_text').append(['layer','"F.Fab"'])
        with self.assertRaises(ValueError):intent.audit(wrong,project)
        wrong=copy.deepcopy(tree);wrong.append(['unknown_item',['layers','"Edge.Cuts"','"F.Cu"']])
        self.assertFalse(intent.audit(wrong,project)['source_intent_allowed'])
    def test_profile_name_prefix_and_inactive_machining_defaults(self):
        _,project,scene=self.prepare('missing_named_profile');raw=raw_report('missing_named_profile',scene,self.ignored)
        for key in ('POWER','MissingOwnedProfile'):
            wrong=copy.deepcopy(raw);wrong['violations'][0]['description']=wrong['violations'][0]['description'].replace(key,key+'Extra')
            self.assertFalse(checks.predicate('missing_named_profile',checks.summary(wrong),wrong,scene,self.ignored)['predicate_met'])
        _,project,scene=self.prepare('positive');native=model(scene,project)
        native['pads'][0]['post_machining']['front']['size_nm']=1200000
        native['pads'][0]['post_machining']['front']['depth_nm']=200000
        self.assertTrue(checks.observe(native,scene,project)['intent_and_geometry_observed'])
    def test_all_six_observation_models_and_predicates(self):
        for case in fx.CASES:
            _,project,scene=self.prepare(case);native=model(scene,project)
            self.assertTrue(checks.observe(native,scene,project)['intent_and_geometry_observed'])
            raw=raw_report(case,scene,self.ignored);before=copy.deepcopy(raw);result=checks.predicate(case,checks.summary(raw),raw,scene,self.ignored)
            self.assertTrue(result['predicate_met'],case);self.assertEqual(raw,before)
            if case=='missing_default_profile':
                self.assertFalse(result['provider_detected']);self.assertEqual(result['coverage_outcome'],'finding_omitted_despite_loaded_intent')
    def test_exact_layer_id_label_and_inherited_class_must_match(self):
        for case in fx.CASES:
            _,project,scene=self.prepare(case)
            for variant in ('id','bool_id','label','parent','class'):
                native=model(scene,project)
                if variant=='id':native['texts'][0]['layer_id']+=2
                if variant=='bool_id':native['texts'][0]['layer_id']=True
                if variant=='label':native['texts'][0]['layer']='Dwgs.User'
                if variant=='parent':native['texts'][0]['parent']='Wrong'
                if variant=='class':native['nets'][0]['class']='POWER' if case=='missing_default_profile' else 'POWER,Default'
                with self.subTest(case=case,variant=variant),self.assertRaises(ValueError):checks.observe(native,scene,project)
    def test_default_present_is_separately_recorded_no_implicit_parity(self):
        _,_,scene=self.prepare('missing_default_profile');raw=raw_report('missing_named_profile',scene,self.ignored)
        raw['violations'][0]['description']=raw['violations'][0]['description'].replace('POWER','Default')
        result=checks.predicate('missing_default_profile',checks.summary(raw),raw,scene,self.ignored)
        self.assertTrue(result['predicate_met']);self.assertTrue(result['provider_detected']);self.assertFalse(result['schematic_parity_qualified'])
    def test_native_profile_normalization_layer_geometry_floor_failures(self):
        for case,variant in (('missing_named_profile','profile'),('missing_default_profile','profile'),('pad_front_counterbore','mode'),('pad_front_counterbore','layer'),('positive','floor'),('positive','terminal'),('positive','track')):
            _,project,scene=self.prepare(case);native=model(scene,project)
            if variant=='profile':
                for row in native['nets']:row['tuning_profile']='';row['has_tuning_profile']=False
            if variant=='mode':native['pads'][2]['post_machining']['front']['mode']='NOT_POST_MACHINED'
            if variant=='layer':native['pads'][2]['affected_layers']=[]
            if variant=='floor':native['floors_nm']['min_clearance']+=1
            if variant=='terminal':native['pads'][0]['net']='Wrong'
            if variant=='track':native['routes']=copy.deepcopy(native['routes']);native['routes'][0]['width_nm']-=1
            with self.subTest(case=case,variant=variant),self.assertRaises(ValueError):checks.observe(native,scene,project)
    def test_negative_target_falsifiers_preserve_raw(self):
        for case in ('missing_named_profile','board_edge_text','footprint_edge_text','pad_front_counterbore'):
            _,_,scene=self.prepare(case)
            for variant in ('none','duplicate','wrong_severity','excluded','wrong_identity','other_error','critical_warning','unknown_warning','parity','open'):
                raw=raw_report(case,scene,self.ignored);target=raw['violations'][0]
                if variant=='none':raw['violations']=[]
                if variant=='duplicate':raw['violations'].append(copy.deepcopy(target))
                if variant=='wrong_severity':target['severity']='error' if case=='missing_named_profile' else 'warning'
                if variant=='excluded':target['excluded']=True
                if variant=='wrong_identity':
                    if case=='missing_named_profile':target['description']='unrelated profile'
                    else:target['items'][0]['uuid']='unrelated'
                if variant=='other_error':raw['violations'].append({'type':'clearance','severity':'error','items':[]})
                if variant=='critical_warning':raw['violations'].append({'type':'padstack_invalid','severity':'warning','items':[]})
                if variant=='unknown_warning':raw['violations'].append({'type':'unknown_provider','severity':'warning','items':[]})
                if variant=='parity':raw['schematic_parity']=[{'type':'footprint_symbol_field_mismatch','severity':'warning','items':[]}]
                if variant=='open':raw['unconnected_items']=[{'type':'unconnected_items','severity':'error','items':[]}]
                before=copy.deepcopy(raw)
                with self.subTest(case=case,variant=variant):self.assertFalse(checks.predicate(case,checks.summary(raw),raw,scene,self.ignored)['predicate_met']);self.assertEqual(raw,before)
    def test_native_ignored_default_exact_and_no_severity_relaxation(self):
        _,_,scene=self.prepare('positive')
        for keys in (self.ignored[:-1],self.ignored+[self.ignored[0]],self.ignored+['clearance']):
            raw=raw_report('positive',scene,keys);self.assertFalse(checks.predicate('positive',checks.summary(raw),raw,scene,self.ignored)['predicate_met'])
        _,project,_=self.prepare('missing_named_profile');project['board']['design_settings']['rule_severities']['missing_tuning_profile']='ignore'
        with self.assertRaises(ValueError):fx.project_delta(self.project,project,'missing_named_profile')
    def record(self):return {'status':'controls_passed','controls_passed':True,**d.FALSE_CLAIMS}
    def test_final_publication_stale_cancel_return_file_and_cap(self):
        for variant in ('positive','canonical','return','cap','cancel','stale'):
            out=self.out/variant;out.mkdir();record=self.record();expired=[];calls=[]
            def scan(_):
                if variant=='canonical':r=d.read(out/'summary.json');r['routing_accepted']=True;d.p.save_json(out/'summary.json',r)
                if variant=='return':record['routing_accepted']=True
                if variant=='cap':expired.append(1)
                return 0
            def stable():
                calls.append(1)
                if len(calls)==2:
                    if variant=='cancel':raise KeyboardInterrupt
                    if variant=='stale':raise ValueError('changed material')
            with mock.patch.object(d,'size',side_effect=scan):result=d.publish(out,record,stable,lambda:None,lambda:0 if expired else 1)
            self.assertIs(result['controls_passed'],variant=='positive');self.assertEqual(result,d.read(out/'summary.json'));self.assertFalse(result['routing_accepted'])
    def test_exact_reviewer_late_scan_source_and_report_mutations(self):
        # Same three real-file cases as the independent publication reproducer.
        for variant in ('unchanged','late_source','late_report'):
            case=self.out/variant;case.mkdir();out=case/'out';out.mkdir()
            source=case/'original.kicad_pro';source.write_text('{"original":true}\n')
            report=out/'raw-report.json';report.write_text('{"violations":[]}\n')
            frozen={source:d.digest(source),report:d.digest(report)};record=self.record();calls=[]
            def stable():
                calls.append('stable')
                if any(d.digest(path)!=digest for path,digest in frozen.items()):raise d.p.Rejected('material changed')
            real_size=d.size
            def final_scan(path):
                measured=real_size(path)
                if variant!='unchanged':
                    target=source if variant=='late_source' else report
                    target.write_bytes(target.read_bytes()+b' ')
                calls.append('size');return measured
            with mock.patch.object(d,'size',side_effect=final_scan):result=d.publish(out,record,stable,lambda:None,lambda:1)
            self.assertIs(result['controls_passed'],variant=='unchanged')
            self.assertIs(d.read(out/'summary.json')['controls_passed'],variant=='unchanged')
            self.assertEqual(calls,['stable','size','stable'])
    def test_failed_correction_removes_positive_canonical(self):
        save=d.p.save_json;calls=[]
        def write(path,value):
            calls.append(1)
            if len(calls)>1:raise OSError('corrective failure')
            save(path,value)
        with mock.patch.object(d.p,'save_json',side_effect=write):result=d.publish(self.out,self.record(),mock.Mock(side_effect=[None,KeyboardInterrupt]),lambda:None,lambda:1)
        self.assertFalse(result['controls_passed']);self.assertFalse((self.out/'summary.json').exists());self.assertTrue(list(self.out.glob('invalidated-*')))
    def test_real_scoped_self_signals_restored(self):
        root=self.out/'root';(root/'.runs').mkdir(parents=True)
        for sig in (signal.SIGINT,signal.SIGTERM):
            previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
            def execute(*args,**kwargs):return d.publish(root/'.runs',self.record(),lambda:os.kill(os.getpid(),sig),lambda:None,lambda:1)
            with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'experiment',side_effect=execute),mock.patch('builtins.print'):
                self.assertEqual(d.main(['--output',str(root/'.runs/out'),'--run-native']),2)
            self.assertEqual(previous,{s:signal.getsignal(s) for s in previous})
    def test_exact_commands_no_save_parity_dsn_or_engine(self):
        job=object.__new__(d.ControlJob);job.out=self.out;job.batch=self.out;job.remaining=lambda:1
        for name,argv in [('engine',['java']),('original-drc',d.drc_argv(self.out)+['--save-board']),('original-drc',d.drc_argv(self.out)+['--schematic-parity']),('observe',d.observe_argv(self.out)+['DSN'])]:
            with self.assertRaises(d.p.Rejected),mock.patch.object(d,'run') as runner:job.step(name,argv,already_sandboxed=True)
            runner.assert_not_called()
        self.assertEqual(d.drc_argv(self.out).count('--refill-zones'),1)
    def test_budget_and_source_committed_snapshot_preconditions(self):
        job=object.__new__(d.ControlJob);job.out=self.out;job.batch=self.out;job.remaining=lambda:0
        with mock.patch.object(d,'run') as run:
            with self.assertRaises(d.p.Rejected):job.step('observe',d.observe_argv(self.out),already_sandboxed=True)
        run.assert_not_called()
        with mock.patch.object(d.subprocess,'run',return_value=type('R',(),{'stdout':b'changed'})()):
            with self.assertRaisesRegex(d.p.Rejected,'commit exact'):d.snapshot(self.out,{'git_head':'mock','implementation_sha256':{}})
    def test_whole_flow_real_file_mutations_with_only_mocked_native_workers(self):
        for variant in ('unchanged','positive_failed','wrong_observation','parsed_observation','parsed_drc','parsed_binding','late_case','late_source','late_helper','late_tool'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory(dir=self.out,prefix=variant+'-') as temp:
                root=Path(temp);(root/'.runs').mkdir();source=root/'source';shutil.copytree(d.SOURCE.parent,source);board=source/d.SOURCE.name
                baseline=root/d.BASELINE_REPORT_REL;baseline.parent.mkdir(parents=True);shutil.copyfile(d.ROOT/d.BASELINE_REPORT_REL,baseline)
                receipt=root/'manifest.json';receipt.write_text('{}');helper=root/'helper.py';helper.write_text('# synthetic helper\n');tool=root/'tool';tool.write_text('mock tool never executed')
                wrapper=root/'wrapper.py';wrapper.write_text('# mock wrapper\n');out=root/'.runs/batch';mutated=[];calls=[]
                hashes=d.inventory(source);total=sum((source/name).stat().st_size for name in hashes)
                tools={'git_head':'mock','implementation_sha256':{},'files':{str(tool):d.digest(tool)}};read=d.read;parse=d.p.parse_report
                def snapshot(out,tools,remaining):
                    (out/'code').mkdir();shutil.copyfile(helper,out/'code/helper.py');return {'helper.py':d.digest(helper)}
                def manifest():
                    if variant in ('late_source','late_helper','late_tool') and (out/'summary.json').exists() and not mutated:
                        target={'late_source':board.with_suffix('.kicad_pro'),'late_helper':helper,'late_tool':tool}[variant];target.write_bytes(target.read_bytes()+b'\n');mutated.append(variant)
                    return tools
                def reader(path):
                    value=read(path)
                    if variant=='parsed_observation' and Path(path).name=='observation.json' and not mutated:
                        changed=copy.deepcopy(value);changed['floors_nm']['min_clearance']+=1;d.p.save_json(Path(path),changed);mutated.append(variant)
                    return value
                def parser(path,name):
                    value=parse(path,name)
                    if variant in ('parsed_drc','parsed_binding') and not mutated:
                        target=Path(path) if variant=='parsed_drc' else Path(path).with_name('original-drc-binding.json')
                        changed=read(target);changed['post_parse_change']=True;d.p.save_json(target,changed);mutated.append(variant)
                    return value
                def runner(argv,**kwargs):
                    directory=kwargs['cwd'];stage=kwargs['log'].stem;case=directory.name;_,project,scene=self.prepare(case)
                    kwargs['log'].write_text('MOCK native stage; no process launched\n');calls.append((case,stage));exit_code=0
                    if stage=='observe':
                        value=model(scene,project);input_board=directory/'observe-input'/board.name;tree=d.inventory(input_board.parent)
                        value.update(source=str(input_board),board_sha256=tree[board.name],project_sha256=tree[board.with_suffix('.kicad_pro').name],input_hashes_before=tree,input_hashes_after=tree)
                        if variant=='wrong_observation' and not mutated:value['nets'][0]['width_nm']-=1;mutated.append(variant)
                        d.p.save_json(directory/'observation.json',value)
                        if variant=='late_case' and case=='missing_named_profile' and not mutated:
                            target=out/'positive/observe-input'/board.with_suffix('.kicad_pro').name;target.write_bytes(target.read_bytes()+b'\n');mutated.append(variant)
                    else:
                        raw=raw_report(case,scene,self.ignored)
                        if variant=='positive_failed' and case=='positive':raw['violations']=[{'type':'clearance','severity':'error','items':[]}];mutated.append(variant)
                        d.p.save_json(directory/'original-drc.json',raw);exit_code=5 if checks.summary(raw)['findings'] else 0
                    return {'status':'nonzero_exit' if exit_code else 'success','exit_code':exit_code,'cleanup_complete':True,'argv':argv,'cwd':str(directory),'cpu_seconds':0,'monitor_cpu_seconds':0}
                with mock.patch.object(d,'ROOT',root),mock.patch.object(d,'SOURCE',board),mock.patch.object(d,'RECEIPT',receipt),mock.patch.object(d,'RECEIPT_SHA',d.digest(receipt)),mock.patch.object(d,'WRAPPER',wrapper),mock.patch.object(d,'WRAPPER_SHA',d.digest(wrapper)),mock.patch.object(d,'source_binding',return_value=(hashes,total)),mock.patch.object(d,'snapshot',side_effect=snapshot),mock.patch.object(d.p,'tool_manifest',side_effect=manifest),mock.patch.object(d.p,'check_storage'),mock.patch.object(d,'run',side_effect=runner),mock.patch.object(d,'read',side_effect=reader),mock.patch.object(d.p,'parse_report',side_effect=parser):
                    result=d.experiment(out,run_native=True)
                self.assertIs(result['controls_passed'],variant=='unchanged',result);self.assertEqual(result,read(out/'summary.json'));self.assertEqual(len(result['cases']),6)
                self.assertFalse(result['schematic_parity_qualified']);self.assertFalse(result['production_support_changed'])
                if variant=='unchanged':self.assertEqual(len(calls),12);self.assertEqual(d.inventory(source),hashes)
                else:self.assertTrue(mutated)
                if variant=='positive_failed':self.assertTrue(all(r['predicate']['predicate_met'] and not r['control_passed'] for r in result['cases'][1:]))
                if variant=='wrong_observation':self.assertNotIn(('positive','original-drc'),calls)

if __name__=='__main__':unittest.main()
