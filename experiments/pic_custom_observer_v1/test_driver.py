"""Pure controls: synthetic observations never establish native/API correctness."""
import copy,hashlib,importlib.util,json,os,shutil,signal,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
import driver as d
import mapping as m
import worker as w
from autorouter.adapter import _parse_dsn, _dump_dsn, _QUOTE_SENTINEL

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def fabricated(notes,project,board,hashes):
    """Synthetic full census with explicitly non-geometric zero world positions."""
    assignment={x['pattern']:x['netclass'] for x in project['net_settings']['netclass_patterns']}
    classes={x['name']:x for x in project['net_settings']['classes']}
    names=notes['source_nonempty_nets'];codes={name:i+1 for i,name in enumerate(names)}
    pads=[dict(uuid=uid,**row,netcode=codes.get(row['net'],0),position_nm=[0,0]) for uid,row in notes['source_pads_identity'].items()]
    nets=[]
    for name in names:
        cls=classes[assignment.get(name,'Default')]
        nets.append({'name':name,'netcode':codes[name],'class':cls['name'],'copper_pad_count':sum(x['net']==name and bool(x['copper_layers']) for x in pads),
            **{a:int(m.Decimal(str(cls[b]))*1000000) for a,b in [('width_nm','track_width'),('clearance_nm','clearance'),('via_diameter_nm','via_diameter'),('via_drill_nm','via_drill')]}})
    native={'context_schema':1,'native_version':'10.0.0','units':'integer nanometres','mode':'export','source':str(board),
        'board_sha256':hashes[board.name],'project_sha256':hashes[board.with_suffix('.kicad_pro').name],
        'input_hashes_before':hashes,'input_hashes_after':hashes,'limits':d.f.LIMITS,'board_saved':False,'routing_accepted':False,
        'floors_nm':{key:int(m.Decimal(str(project['board']['design_settings']['rules'][key]))*1000000) for key in m.g.FLOORS},
        'nets':nets,'pads':pads,'routes':[{'uuid':uid} for uid in notes['source_route_ids']],'obstacles':[]}
    fps={r['reference']:r['uuid'] for r in notes['source_footprints']}
    customs=[]
    for row in notes['custom_pads']:
        node=row['pad_ast'];poly=d.sx.one(d.sx.one(node,'primitives'),'gr_poly')
        points=[[int(m.Decimal(v)*1000000) for v in p[1:]] for p in d.sx.one(poly,'pts')[1:]]
        shape={'arc_count':0,'outlines':[{'outline':{'closed':True,'points_nm':points},'holes':[]}],'total_vertices':len(points)}
        customs.append({**{key:row[key] for key in ('uuid','reference','number','net','copper_layers','footprint_uuid')},
            'netcode':codes[row['net']],'position_nm':[0,0],'shape':'custom','anchor':'rect','attribute':'smd',
            'size_nm':[300000,300000],'offset_nm':[0,0],'drill_nm':[0,0],
            'merged_local':shape,'transformed_world':copy.deepcopy(shape),'effective_world':copy.deepcopy(shape)})
    census={'schema':1,'total_pad_count':len(pads),'pads':customs,'routing_accepted':False,'geometry_qualified':False,
        'all_terminals':[{**row,'footprint_uuid':fps[row['reference']]} for row in pads],
        'all_footprints':[{key:row[key] for key in ('uuid','reference','layer')} for row in notes['source_footprints']]}
    custom={**{key:native[key] for key in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','input_hashes_before','input_hashes_after')},
        'board_saved':False,'routing_accepted':False,'geometry_qualified':False,'same_loaded_board':True,
        'observation_before_export':census,'observation_after_export':copy.deepcopy(census)}
    stacks=[['padstack','plain',['shape',['circle','F.Cu','100']]]]
    custom_ids={r['uuid']:'custom_'+r['number'] for r in customs}
    for row in customs:
        stacks.append(['padstack',custom_ids[row['uuid']],['shape',['polygon','B.Cu','0','0','0','100','0','0','100','0','0']]])
    images=[];components=[]
    for ref in fps:
        pins=[];used={}
        for row in [r for r in pads if r['reference']==ref]:
            number=row['number'];index=used.get(number,0);used[number]=index+1
            unique=number if number and index==0 else number+'@'+str(index if number else index+1)
            pins.append(['pin',custom_ids.get(row['uuid'],'plain'),'"'+unique+'"','0','0'])
        images.append(['image',ref,*pins]);components.append(['component',ref,['place',ref,'0','0','front','0']])
    network=['network',*[['net','"'+name+'"',['pins',*[row['reference']+'-'+row['number'] for row in pads if row['net']==name and row['copper_layers']]]] for name in names]]
    raw=_dump_dsn(['pcb','synthetic',['parser',['string_quote',_QUOTE_SENTINEL]],['unit','um'],['resolution','um','10'],['library',*images,*stacks],['placement',*components],network]).encode()
    native['dsn_sha256']=custom['dsn_sha256']=d.sha_bytes(raw)
    return native,custom,raw

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes,cls.total=d.source_binding();cls.board=d.sx.read(d.SOURCE);cls.project=d.read(d.SOURCE.with_suffix('.kicad_pro'))
        cls.notes=d.source_notes(cls.board,cls.project)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=d.HERE,prefix='pure-');self.out=Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
    def context(self):return fabricated(self.notes,self.project,self.out/'observe-input'/d.SOURCE.name,self.hashes)
    def write_context(self):
        native,custom,raw=self.context();(self.out/'native.dsn').write_bytes(raw)
        d.p.save_json(self.out/'observation.json',native);custom['floor_context_sha256']=digest(self.out/'observation.json');d.p.save_json(self.out/'custom-pads.json',custom)
        return native,custom,raw
    def test_complete_original_source_stays_blocked(self):
        self.assertEqual((len(self.hashes),self.total),(15,1366598))
        with self.assertRaises(d.p.Rejected) as cm:d.p.preflight(d.SOURCE)
        self.assertEqual(str(cm.exception),d.EXPECTED_GATE)
    def test_source_manifest_digest_changed(self):
        with mock.patch.object(d,'RECEIPT_SHA','0'*64):
            with self.assertRaisesRegex(d.p.Rejected,'manifest'):d.source_binding()
    def test_source_recipe_keeps_routes_and_severities(self):
        self.assertEqual(len(self.notes['source_route_ids']),376)
        self.assertEqual(self.notes['new_severity_intent'],m.SEVERITIES)
        self.assertFalse(self.notes['geometry_qualified'])
        altered=copy.deepcopy(self.project);altered['board']['design_settings']['rule_severities']['text_on_edge_cuts']='ignore'
        with self.assertRaisesRegex(ValueError,'severity'):d.source_notes(self.board,altered)
    def test_observation_false_scope_positive(self):
        self.write_context();result=d.observe_binding(self.out,self.hashes,self.notes)
        self.assertEqual(len(result['custom_pad_observation']['observation_before_export']['pads']),2)
        self.assertFalse(result['dsn_correspondence']['geometry_qualified'])
    def test_full_terminal_mutation_after_export_rejects(self):
        native,custom,raw=self.context();custom['observation_after_export']['all_terminals'][0]['net']='tampered'
        with self.assertRaisesRegex(ValueError,'restore'):m.custom_identity(custom,native,self.notes)
    def test_full_terminal_rehashed_same_prepost_mutation_rejects(self):
        native,custom,raw=self.context()
        for key in ('observation_before_export','observation_after_export'):custom[key]['all_terminals'][0]['position_nm']=[99,99]
        with self.assertRaisesRegex(ValueError,'mapping'):m.custom_identity(custom,native,self.notes)
    def test_custom_pad_uuid_net_anchor_layer_reject(self):
        for key,value in [('uuid','wrong'),('net','wrong'),('anchor','circle'),('drill_nm',[1,1]),('copper_layers',['F.Cu'])]:
            native,custom,raw=self.context()
            for which in ('observation_before_export','observation_after_export'):custom[which]['pads'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.custom_identity(custom,native,self.notes)
    def test_shape_malformed_or_unclosed_rejects(self):
        for key,value in [('arc_count',1),('total_vertices',1000)]:
            native,custom,raw=self.context()
            for which in ('observation_before_export','observation_after_export'):custom[which]['pads'][0]['effective_world'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.custom_identity(custom,native,self.notes)
    def test_context_and_custom_hash_rebind_rejects(self):
        self.write_context();custom=d.read(self.out/'custom-pads.json');custom['project_sha256']='0'*64;d.p.save_json(self.out/'custom-pads.json',custom)
        with self.assertRaisesRegex(d.p.Rejected,'binding'):d.observe_binding(self.out,self.hashes,self.notes)
    def test_dsn_terminal_reassigned_rejects(self):
        native,custom,raw=self.context();tree=_parse_dsn(raw.decode());nets=d.sx.children(d.sx.one(tree,'network'),'net');nets[0][1]='"wrong"'
        with self.assertRaisesRegex(ValueError,'terminal'):m.dsn_correspondence(_dump_dsn(tree).encode(),native,custom['observation_before_export']['pads'])
    def test_dsn_padstack_loss_rejects(self):
        native,custom,raw=self.context();tree=_parse_dsn(raw.decode());library=d.sx.one(tree,'library');library.remove(next(x for x in d.sx.children(library,'padstack') if x[1]=='custom_1'))
        with self.assertRaisesRegex(ValueError,'padstack'):m.dsn_correspondence(_dump_dsn(tree).encode(),native,custom['observation_before_export']['pads'])
    def test_dsn_wrong_units_rejects(self):
        native,custom,raw=self.context();raw=raw.replace(b'(unit um)',b'(unit mm)')
        with self.assertRaisesRegex(ValueError,'unit'):m.dsn_correspondence(raw,native,custom['observation_before_export']['pads'])
    def retained_export(self):
        """Actual native001 artifacts; reading them does not rerun native validation."""
        base=d.ROOT/'evidence/pic-custom-observation-001'
        expected={'native.dsn':'d928e7f3e823dd9c3adbe8cc09e5cd65c17c014e1377076fee8f94336e652111',
            'observation.json':'badfc2effcb330ce57e44bc385ac618bb8ba4f0d3cc217bb8ac4c24c2bbebb72',
            'custom-pads.json':'a332de64029ba810c3526b331a59a7d6fcd443c648a7b4a7fc7148353a389baf'}
        for name,sha in expected.items():self.assertEqual(digest(base/name),sha,name)
        return d.read(base/'observation.json'),d.read(base/'custom-pads.json'),(base/'native.dsn').read_bytes()
    def test_actual_export_quote_grammar_and_complete_correspondence(self):
        native,custom,raw=self.retained_export()
        self.assertEqual(raw.count(b'(string_quote ")'),1)
        with self.assertRaisesRegex(ValueError,'invalid S-expression token'):d.sx.parse(raw.decode())
        self.assertEqual(_parse_dsn(raw.decode())[0],'pcb')
        m.floor_identity(native,self.notes,self.project)
        pads=m.custom_identity(custom,native,self.notes)
        result=m.dsn_correspondence(raw,native,pads)
        self.assertEqual(result['terminal_count'],236);self.assertEqual(len(result['custom_pads']),2)
        self.assertEqual((len(native['pads']),len(native['routes'])),(247,376))
        self.assertFalse(result['geometry_qualified']);self.assertFalse(result['routing_accepted'])
    def test_actual_export_missing_duplicate_or_misplaced_quote_rejects(self):
        native,custom,raw=self.retained_export();declaration=b'(string_quote ")'
        missing=raw.replace(declaration,b'',1)
        malformed={'missing':missing,'duplicate':raw.replace(declaration,declaration+b' '+declaration,1),
            'outside_parser':missing.replace(b'(structure',declaration+b'\n  (structure',1),
            'unterminated_string':raw+b'\n"unterminated','unbalanced':raw.rstrip()[:-1]}
        self.assertNotEqual(malformed['outside_parser'],missing)
        for name,bad in malformed.items():
            with self.subTest(name=name),self.assertRaises(ValueError):
                m.dsn_correspondence(bad,native,custom['observation_before_export']['pads'])
    def test_actual_export_reserved_quote_sentinel_rejects(self):
        native,custom,raw=self.retained_export()
        with self.assertRaisesRegex(ValueError,'reserved quote sentinel'):
            m.dsn_correspondence(raw+b'\n; '+_QUOTE_SENTINEL.encode(),native,custom['observation_before_export']['pads'])
    def test_actual_export_reassigned_terminal_rejects_after_parse(self):
        native,custom,raw=self.retained_export();tree=_parse_dsn(raw.decode())
        d.sx.children(d.sx.one(tree,'network'),'net')[0][1]='"wrong-assigned-net"'
        with self.assertRaisesRegex(ValueError,'terminal mismatch'):
            m.dsn_correspondence(_dump_dsn(tree).encode(),native,custom['observation_before_export']['pads'])
    def test_actual_export_missing_custom_padstack_rejects_after_parse(self):
        native,custom,raw=self.retained_export();rows=custom['observation_before_export']['pads']
        result=m.dsn_correspondence(raw,native,rows);stack_name=result['custom_pads'][0]['padstack_ast'][1]
        tree=_parse_dsn(raw.decode());library=d.sx.one(tree,'library')
        library.remove(next(node for node in d.sx.children(library,'padstack') if node[1]==stack_name))
        with self.assertRaisesRegex(ValueError,'padstack'):
            m.dsn_correspondence(_dump_dsn(tree).encode(),native,rows)
    def test_context_flag_path_argument_guards(self):
        with self.assertRaisesRegex(d.p.Rejected,'run-native'):d.experiment(self.out/'absent')
        for value in ('export','context-only',None,True):
            with self.assertRaisesRegex(d.p.Rejected,'unknown'):d.observation_mode(value)
        link=self.out/'link';link.symlink_to(d.SOURCE)
        with self.assertRaises(d.p.Rejected):d.owned(link)
    def test_exact_argv_rejects_engine_save_and_other_worker(self):
        job=object.__new__(d.ObservationJob);job.out=self.out;job.observation='custom-pad-export';job.remaining=lambda:60
        with mock.patch.object(d,'run') as run:
            for name,argv in [('engine',['java']),('observe',d.observe_argv(self.out)+['extra']),('original-drc',d.drc_argv(self.out)+['--save-board'])]:
                with self.assertRaisesRegex(d.p.Rejected,'exact nonsaving'):job.step(name,argv,already_sandboxed=True)
        run.assert_not_called()
    def test_stage_capture_precedes_caller_parse(self):
        job=object.__new__(d.ObservationJob);job.out=self.out;job.observation='custom-pad-export';job.remaining=lambda:60;job.env={};job.steps=[];job.stage_evidence={}
        def fake(argv,**kwargs):
            for name in ('observation.json','native.dsn','custom-pads.json','observe.log'):(self.out/name).write_bytes(b'original')
            return {'status':'success','exit_code':0,'cleanup_complete':True,'cpu_seconds':0}
        with mock.patch.object(d,'run',side_effect=fake):job.step('observe',d.observe_argv(self.out),already_sandboxed=True)
        saved=job.stage_evidence['observe']['custom-pads.json'];(self.out/'custom-pads.json').write_bytes(b'changed')
        self.assertNotEqual(saved,digest(self.out/'custom-pads.json'))
    def test_budget_before_worker_and_copy_reservation(self):
        job=object.__new__(d.ObservationJob);job.out=self.out;job.observation='custom-pad-export';job.remaining=lambda:0
        with mock.patch.object(d,'run') as run:
            with self.assertRaisesRegex(d.p.Rejected,'budget'):job.step('observe',d.observe_argv(self.out),already_sandboxed=True)
        run.assert_not_called()
        with mock.patch.object(d,'size',return_value=d.LIMIT-self.total):
            with self.assertRaisesRegex(d.p.Rejected,'ceiling'):d.reserve_copy(self.out,self.total,2)
    def test_snapshot_commit_mismatch_rejects(self):
        with mock.patch.object(d.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'changed',b'')):
            with self.assertRaisesRegex(d.p.Rejected,'commit exact'):d.snapshot(self.out,{'git_head':'mock','implementation_sha256':{}})
        self.assertFalse((self.out/'code').exists())
    def record(self):return {'status':'observations_complete','observations_complete':True,'routing_accepted':False,'geometry_qualified':False}
    def test_publication_positive_false_qualification(self):
        record=d.publish(self.out,self.record(),lambda:None,lambda:None,lambda:1)
        self.assertTrue(record['observations_complete']);self.assertFalse(record['geometry_qualified'])
    def test_final_stale_cancel_cap_and_canonical_reject(self):
        for label in ('stale','cancel','cap','canonical'):
            out=self.out/label;out.mkdir();calls=[]
            def stable():
                calls.append(1)
                if len(calls)==2:
                    if label=='stale':raise ValueError('changed material')
                    if label=='cancel':raise KeyboardInterrupt
                    if label=='canonical':
                        raw=d.read(out/'summary.json');raw['geometry_qualified']=True;d.p.save_json(out/'summary.json',raw)
            row=d.publish(out,self.record(),stable,lambda:None,lambda:0 if label=='cap' else 1)
            self.assertFalse(row['observations_complete']);self.assertFalse(d.read(out/'summary.json')['geometry_qualified'])
            self.assertTrue(list(out.glob('invalidated-*')))
    def test_failed_correction_preserves_invalidated_not_positive(self):
        save=d.p.save_json;calls=[]
        def broken(path,data):
            calls.append(1)
            if len(calls)>1:raise OSError('failed correction')
            save(path,data)
        with mock.patch.object(d.p,'save_json',side_effect=broken):
            row=d.publish(self.out,self.record(),mock.Mock(side_effect=[None,KeyboardInterrupt]),lambda:None,lambda:1)
        self.assertFalse(row['observations_complete']);self.assertFalse((self.out/'summary.json').exists())
    def test_final_size_scan_cannot_change_canonical(self):
        def size(out):
            raw=d.read(out/'summary.json');raw['geometry_qualified']=True;d.p.save_json(out/'summary.json',raw);return 0
        with mock.patch.object(d,'size',side_effect=size):result=d.publish(self.out,self.record(),lambda:None,lambda:None,lambda:1)
        self.assertFalse(result['observations_complete']);self.assertFalse(d.read(self.out/'summary.json')['geometry_qualified'])
        self.assertTrue(list(self.out.glob('invalidated-*summary.json')))
    def test_final_size_scan_cannot_expire_budget_unnoticed(self):
        expired=[]
        def size(out):expired.append(1);return 0
        with mock.patch.object(d,'size',side_effect=size):result=d.publish(self.out,self.record(),lambda:None,lambda:None,lambda:0 if expired else 1)
        self.assertFalse(result['observations_complete']);self.assertFalse(d.read(self.out/'summary.json')['observations_complete'])
    def test_final_size_scan_cannot_change_returned_record(self):
        record=self.record()
        def size(out):record['geometry_qualified']=True;return 0
        with mock.patch.object(d,'size',side_effect=size):result=d.publish(self.out,record,lambda:None,lambda:None,lambda:1)
        self.assertFalse(result['observations_complete']);self.assertFalse(result['geometry_qualified'])
        self.assertEqual(d.read(self.out/'summary.json'),result)
    def test_final_invalidation_preserves_first_diagnostic_failure(self):
        record=self.record();record.update(status='failed',observations_complete=False,error='ValueError: original mapping failure')
        result=d.publish(self.out,record,mock.Mock(side_effect=ValueError('later material failure')),lambda:None,lambda:1)
        self.assertEqual(result['error'],'ValueError: original mapping failure')
        self.assertEqual(result['final_validation_error'],'ValueError: later material failure')
        self.assertFalse(result['observations_complete'])
    def test_signal_handlers_scoped_and_restore(self):
        base=self.out/'root';(base/'.runs').mkdir(parents=True)
        for sig in (signal.SIGINT,signal.SIGTERM):
            previous={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
            def experiment(*a,**kw):
                return d.publish(base/'.runs',self.record(),lambda:os.kill(os.getpid(),sig),lambda:None,lambda:1)
            with mock.patch.object(d,'ROOT',base),mock.patch.object(d,'experiment',side_effect=experiment),mock.patch('builtins.print'):
                self.assertEqual(d.main(['--run-native','--output',str(base/'.runs/out')]),2)
            self.assertEqual({s:signal.getsignal(s) for s in previous},previous)
            for file in (base/'.runs').glob('summary.json'):file.unlink()

    def test_whole_flow_stage_and_final_material_falsifiers(self):
        for variant in ('unchanged','mapping_failure','parsed_context','parsed_drc','late_source','late_helper','late_tool','late_custom'):
            with self.subTest(variant=variant):
                base=self.out/variant;(base/'.runs').mkdir(parents=True);source=base/'source';source.mkdir()
                for path in (d.SOURCE,d.SOURCE.with_suffix('.kicad_pro')):shutil.copyfile(path,source/path.name)
                board=source/d.SOURCE.name;receipt=base/'acquisition.json';receipt.write_text('{"synthetic_scope":true}')
                helper=base/'helper.py';helper.write_bytes(b'# frozen mocked helper\n')
                tool=base/'tool';tool.write_bytes(b'not executable')
                hashes=d.inventory(source);total=sum(path.stat().st_size for path in source.iterdir());out=base/'.runs/out'
                tools={'git_head':'mocked','implementation_sha256':{},'files':{str(tool):digest(tool)}}
                mutated=[];calls=[];real_read=d.read;real_parse=d.p.parse_report
                def snapshot(out,tools,remaining):
                    (out/'code').mkdir();shutil.copy2(helper,out/'code/helper.py');return {'helper.py':digest(helper)}
                def manifest():
                    if variant.startswith('late_') and (out/'summary.json').exists() and not mutated:
                        path={'late_source':board,'late_helper':helper,'late_tool':tool,'late_custom':out/'custom-pads.json'}[variant]
                        path.write_bytes(path.read_bytes()+b'\n');mutated.append(1)
                    return tools
                def read(path):
                    value=real_read(path)
                    if variant=='parsed_context' and Path(path).name=='observation.json' and not mutated:
                        raw=copy.deepcopy(value);raw['floors_nm']['min_clearance']+=1;d.p.save_json(Path(path),raw);mutated.append(1)
                    return value
                def parse(path,name):
                    value=real_parse(path,name)
                    if variant=='parsed_drc' and not mutated:
                        raw=real_read(path);raw['date']='changed after parse';d.p.save_json(Path(path),raw);mutated.append(1)
                    return value
                def run(argv,**kwargs):
                    calls.append(argv);kwargs['log'].write_text('mock native stage; no process launched\n')
                    if kwargs['log'].name=='observe.log':
                        n,custom,raw=fabricated(self.notes,self.project,out/'observe-input'/board.name,hashes)
                        if variant=='mapping_failure':n['pads'][0]['net']='wrong native net';mutated.append(1)
                        (out/'native.dsn').write_bytes(raw);d.p.save_json(out/'observation.json',n)
                        custom['floor_context_sha256']=digest(out/'observation.json');d.p.save_json(out/'custom-pads.json',custom)
                    else:
                        d.p.save_json(out/'original-drc.json',{'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,
                            'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],'included_severities':['error','warning','exclusion']})
                    return {'status':'success','exit_code':0,'cleanup_complete':True,'argv':argv,'cwd':str(out),'cpu_seconds':0,'monitor_cpu_seconds':0}
                with mock.patch.object(d,'ROOT',base),mock.patch.object(d,'SOURCE',board),mock.patch.object(d,'RECEIPT',receipt),mock.patch.object(d,'RECEIPT_SHA',digest(receipt)),mock.patch.object(d,'source_binding',return_value=(hashes,total)),mock.patch.object(d,'snapshot',side_effect=snapshot),mock.patch.object(d.p,'tool_manifest',side_effect=manifest),mock.patch.object(d.p,'check_storage'),mock.patch.object(d,'read',side_effect=read),mock.patch.object(d.p,'parse_report',side_effect=parse),mock.patch.object(d,'run',side_effect=run):
                    result=d.experiment(out,run_native=True)
                self.assertIs(result['observations_complete'],variant=='unchanged',result)
                self.assertIs(real_read(out/'summary.json')['observations_complete'],variant=='unchanged')
                if variant=='unchanged':self.assertEqual(len(calls),2);self.assertEqual(d.inventory(source),hashes)
                else:self.assertTrue(mutated)
                if variant=='mapping_failure':
                    self.assertTrue(result['dsn_export_succeeded']);self.assertFalse(result['correspondence_verified'])
                    self.assertEqual(result['native_dsn_sha256'],digest(out/'native.dsn'))
                    self.assertIn('native original terminal identities differ',result['error']);self.assertNotIn('final_validation_error',result)
                    self.assertEqual(len(calls),1);self.assertFalse(result['geometry_qualified'])

class WorkerGuards(unittest.TestCase):
    def test_polygon_opaque_shared_ptr_fails_honestly(self):
        with self.assertRaises(AttributeError):w.polygon(object())
    def test_polygon_count_and_bool_cap(self):
        with self.assertRaises(ValueError):w.polygon(types.SimpleNamespace(OutlineCount=lambda:5,ArcCount=lambda:0))
        with self.assertRaises(ValueError):w.boolean(1)
        with self.assertRaises(ValueError):w.angle(float('nan'))
    def test_no_wrong_layer_compatibility_helper(self):
        import ast
        tree=ast.parse((d.HERE/'worker.py').read_text())
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr=='GetCustomShapeAsPolygon' for n in ast.walk(tree)))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('MergePrimitivesAsPolygon','GetEffectivePolygon')]
        self.assertEqual(len(calls),2)
        self.assertTrue(all(isinstance(n.args[0],ast.Name) and n.args[0].id=='layer' for n in calls))

    def test_callback_same_loaded_board_prepost_and_default_absent(self):
        path=d.HERE/'autorouter/floor_context.py'
        if not path.is_file():path=d.ROOT/'autorouter/floor_context.py'
        spec=importlib.util.spec_from_file_location('controlled_floor_context',path);fc=importlib.util.module_from_spec(spec);spec.loader.exec_module(fc)
        with tempfile.TemporaryDirectory(dir=d.HERE,prefix='callback-') as tmp:
            out=Path(tmp);source=out/'input';source.mkdir();board=source/'owned.kicad_pcb';board.write_text('owned pure dummy input');board.with_suffix('.kicad_pro').write_text('{}')
            state=[];settings=types.SimpleNamespace(**{value:1000 for value in fc.FLOORS.values()})
            native=types.SimpleNamespace(GetCopperLayerCount=lambda:2,SynchronizeNetsAndNetClasses=lambda _:state.append('sync'),GetPads=lambda:[],GetNetsByName=lambda:{},GetTracks=lambda:[],GetDrawings=lambda:[],GetFootprints=lambda:[],GetDesignSettings=lambda:settings)
            def export(obj,target):self.assertIs(obj,native);state.append('export');Path(target).write_text('(pcb observed)');return True
            pcb=types.SimpleNamespace(GetBuildVersion=lambda:'10.0.0',LoadBoard=mock.Mock(return_value=native),ExportSpecctraDSN=export)
            context=out/'context.json';dsn=out/'native.dsn';extra=out/'extra.json'
            with mock.patch.dict(sys.modules,{'pcbnew':pcb}):fc.collect('export',board,context,dsn)
            old=context.read_bytes();old_dsn=dsn.read_bytes();self.assertFalse(extra.exists());self.assertEqual(state,['sync','export']);pcb.LoadBoard.assert_called_once()
            context.unlink();dsn.unlink();state.clear();pcb.LoadBoard.reset_mock()
            def observer(obj,module):self.assertIs(obj,native);self.assertIs(module,pcb);state.append('observer');return {'fixed':'bounded synthetic'}
            with mock.patch.dict(sys.modules,{'pcbnew':pcb}):fc.collect('export',board,context,dsn,observation_output=extra,observer=observer)
            self.assertEqual(state,['sync','observer','export','observer']);pcb.LoadBoard.assert_called_once()
            self.assertEqual(context.read_bytes(),old);self.assertEqual(dsn.read_bytes(),old_dsn)
            raw=d.read(extra);self.assertEqual(raw['observation_before_export'],raw['observation_after_export']);self.assertEqual(raw['floor_context_sha256'],digest(context))
            for file in (context,dsn,extra):file.unlink()
            with mock.patch.dict(sys.modules,{'pcbnew':pcb}),self.assertRaisesRegex(ValueError,'changed diagnostic'):
                fc.collect('export',board,context,dsn,observation_output=extra,observer=mock.Mock(side_effect=[{'state':0},{'state':1}]))
            self.assertFalse(context.exists());self.assertFalse(extra.exists())
    def test_callback_paths_pair_and_failure_before_export(self):
        path=d.HERE/'autorouter/floor_context.py'
        if not path.is_file():path=d.ROOT/'autorouter/floor_context.py'
        spec=importlib.util.spec_from_file_location('guarded_floor_context',path);fc=importlib.util.module_from_spec(spec);spec.loader.exec_module(fc)
        with tempfile.TemporaryDirectory(dir=d.HERE,prefix='callback-') as tmp:
            out=Path(tmp);source=out/'input';source.mkdir();board=source/'owned.kicad_pcb';board.write_text('dummy');board.with_suffix('.kicad_pro').write_text('{}')
            for kwargs in ({'observer':lambda *_:{}},{'observation_output':out/'extra.json'},{'observer':'not callable','observation_output':out/'extra.json'},{'observer':lambda *_:{},'observation_output':out/'context.json'}):
                with self.assertRaisesRegex(ValueError,'callback/output'):fc.collect('export',board,out/'context.json',out/'native.dsn',**kwargs)
            self.assertFalse((out/'context.json').exists())

if __name__=='__main__':unittest.main()
