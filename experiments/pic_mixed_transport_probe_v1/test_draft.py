"""Pure retained-byte and controlled-stage tests; no native/JVM execution."""
import copy,importlib.util,json,sys,tempfile,unittest
from contextlib import ExitStack
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/runner.py').is_file())
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
import transport
spec=importlib.util.spec_from_file_location('mixed_native_worker',HERE/'worker.py');worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
spec=importlib.util.spec_from_file_location('mixed_controller',HERE/'driver.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
from autorouter import sexpr as sx
from autorouter.adapter import _parse_dsn,_dump_dsn
from experiments.pic_custom_observer_v1 import mapping

class Pure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
        cls.basis=ROOT/'evidence/pic-custom-observation-002'
        cls.raw=(cls.basis/'native.dsn').read_bytes();cls.context=json.loads((cls.basis/'observation.json').read_text());cls.custom=json.loads((cls.basis/'custom-pads.json').read_text())
        cls.notes=mapping.source_notes(sx.read(source),json.loads(source.with_suffix('.kicad_pro').read_text()))
        cls.derived,cls.expected=transport.derive(cls.raw,cls.context,cls.custom,cls.notes)
    def synthetic(self):
        e=self.expected;pins=[]
        for i,p in enumerate(e['dsn_pins']):pins.append({'id':i+1,'reference':p['reference'],'number':p['number'],'nets':copy.deepcopy(p['nets']),
            'position_um':p['position_um'],'padstack_name':'other','clearance_class_index':0,'contacts':[]})
        nets=[{'name':name,'class':v['class'],'width_um':[v['width_um']]*2,'trace_clearance_class':2 if v['class']=='POWER' else 1} for name,v in e['nets'].items()]
        matrix=[{'a':a,'b':b,'layer':l,'raw_um':250,'compensated_um':251.6,'raw_board_units':2500,'compensated_board_units':2516} for a in range(3) for b in range(3) for l in (0,1)]
        result={'schema':1,'routing_executed':False,'ses_executed':False,'cases':[]}
        for flag in (False,True):
            ps=copy.deepcopy(pins);areas=[]
            for i,want in enumerate(e['areas']):
                pin=next(p for p in ps if p['reference']==want['reference'] and p['number']==want['number']);pin['padstack_name']=want['padstack_name'];pin['contacts']=[1000+i]
                areas.append({'id':1000+i,'nets':[want['net']],'layer':want['layer'],'ring_um':want['ring_um'],
                    'ring_board_integer':[[v*10 for v in point] for point in want['ring_um']],'holes':0,
                    'obstacle':flag,'fixed':'USER_FIXED','clearance_class_index':0,'contacts':[pin['id']]})
            state={'nets':nets,'pins':ps,'census':{'pins':len(ps)},'areas':areas,'layers':e['layer_order'],'board_units_per_um':10,
                'board_origin_dsn_um':[0,0],'clearance_class_names':['smd','default','POWER'],'matrix':matrix}
            settings={'plane_as_obstacle':flag,'router_enabled':False,'optimizer_enabled':False}
            result['cases'].append({'requested_obstacle':flag,'input_sha256':e['derived_dsn_sha256'],'status':'observed','post_load_awaited':True,
                'settings_before':copy.deepcopy(settings),'settings_after':copy.deepcopy(settings),'state':state})
        return result
    def test_actual_retained_derive_exact_reverse(self):
        before=_parse_dsn(self.raw.decode());after=_parse_dsn(self.derived.decode())
        wiring=sx.one(after,'wiring');self.assertEqual(len(sx.children(wiring,'wire')),341)
        del wiring[-2:]
        old={sx.unquote(x[1]):x for x in sx.children(sx.one(before,'library'),'padstack')}
        for stack in sx.children(sx.one(after,'library'),'padstack'):
            if sx.unquote(stack[1]) in {a['original_padstack_name'] for a in self.expected['areas']}:stack[:]=copy.deepcopy(old[sx.unquote(stack[1])])
        self.assertEqual(after,before);self.assertEqual(self.expected['terminal_count'],236)
        self.assertEqual([a['native_class'] for a in self.expected['areas']],['POWER','Default'])
        self.assertEqual(self.expected['unchanged_original_plane_count'],1)
        self.assertEqual((self.expected['native_pad_count'],self.expected['dsn_pin_count'],self.expected['dsn_unassigned_pin_count']),(247,240,4))
        unassigned={(p['reference'],p['number']):p['position_um'] for p in self.expected['dsn_pins'] if not p['nets']}
        self.assertEqual(unassigned,{('P3','@1'):[168910,-96520],('P3','@2'):[196850,-48260],('J1','SH'):[81180,-102160],('J1','SH@1'):[81180,-127160]})
    def test_derivation_rejects_name_alias(self):
        tree=_parse_dsn(self.raw.decode());lib=sx.one(tree,'library');stack=copy.deepcopy(sx.children(lib,'padstack')[0]);stack[1]=stack[1]+'.123';lib.append(stack)
        with self.assertRaisesRegex(ValueError,'noninjective'):transport.derive(_dump_dsn(tree).encode(),self.context,self.custom,self.notes)
    def test_original_native_identity_tamper(self):
        changed=copy.deepcopy(self.custom);changed['observation_before_export']['pads'][0]['net']='GND'
        with self.assertRaises(ValueError):transport.derive(self.raw,self.context,changed,self.notes)
    def test_synthetic_observation_and_targeted_mutations(self):
        self.assertTrue(all(r['observed'] for r in transport.validate(self.synthetic(),self.expected)))
        mutations=[lambda x:x['cases'][0]['state']['nets'][0].update({'class':'POWER'}),
            lambda x:x['cases'][0]['state']['nets'][0].update({'width_um':[1,1]}),
            lambda x:x['cases'][0]['state']['pins'][0].update({'nets':['WRONG']}),
            lambda x:x['cases'][0]['state']['matrix'].pop(),
            lambda x:x['cases'][0]['state']['matrix'][0].update({'raw_um':249}),
            lambda x:x['cases'][0]['state']['areas'][0].update({'obstacle':True}),
            lambda x:x['cases'][0]['state']['areas'][0].update({'clearance_class_index':100}),
            lambda x:x['cases'][0]['state']['areas'][0]['ring_board_integer'][0].__setitem__(0,1),
            lambda x:x['cases'][0]['settings_before'].update({'router_enabled':True})]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                changed=self.synthetic();mutation(changed)
                with self.assertRaises((ValueError,KeyError)):transport.validate(changed,self.expected)
    def test_observed_failure_retained(self):
        observation=self.synthetic();observation['cases'][0].update(status='failed',error='actual importer exception')
        result=transport.validate(observation,self.expected);self.assertFalse(result[0]['observed']);self.assertEqual(result[0]['error'],'actual importer exception')
    def test_complete_lifecycle_contract(self):
        mutations=[lambda o:o.update(ses_executed=True),lambda o:o.pop('ses_executed'),lambda o:o.update(schema=True),
            lambda o:o['cases'][0].update(post_load_awaited=False),lambda o:o['cases'][0].pop('post_load_awaited'),
            lambda o:o['cases'][0]['settings_after'].update(router_enabled=True),
            lambda o:o['cases'][0]['settings_after'].update(optimizer_enabled=True),
            lambda o:o['cases'][0]['settings_after'].pop('router_enabled')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                observation=self.synthetic();mutation(observation)
                with self.assertRaises(ValueError):transport.validate(observation,self.expected)
    def test_full_unassigned_import_pin_contract(self):
        mutations=[lambda s:s.update(pins=[p for p in s['pins'] if p['nets']]),
            lambda s:s['pins'].append({'reference':'UNKNOWN','number':'1','nets':[],'position_um':[0,0]}),
            lambda s:next(p for p in s['pins'] if not p['nets']).update(position_um=[0,0]),
            lambda s:next(p for p in s['pins'] if not p['nets']).update(nets=['GND']),
            lambda s:s['census'].update(pins=236)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                observation=self.synthetic();mutation(observation['cases'][0]['state'])
                with self.assertRaises(ValueError):transport.validate(observation,self.expected)
    def test_unfamiliar_placement_transform_rejected(self):
        for side,angle in [('front','45'),('back','90'),('unknown','0')]:
            tree=_parse_dsn(self.raw.decode());place=sx.children(sx.children(sx.one(tree,'placement'),'component')[0],'place')[0];place[4:6]=[side,angle]
            with self.assertRaisesRegex(ValueError,'unqualified DSN placement'):transport.placed_pins(tree)
    def test_optional_never_guesses(self):
        for value in (None,250000):self.assertEqual(worker.optional(lambda:value),{'status':'observed','value_nm':value})
        for value in (True,'250000',object(),250000.0,-1):self.assertEqual(worker.optional(lambda:value)['status'],'unsupported')
        self.assertEqual(worker.optional(lambda:(_ for _ in ()).throw(TypeError()))['error_type'],'TypeError')
    def test_actual_native_extension_pin_and_runtime_change(self):
        protocol=json.loads((HERE/'PROTOCOL.json').read_text());lock=json.loads((ROOT/'toolchain.lock.json').read_text())
        self.assertEqual(protocol['tools']['pcbnew'],lock['tools']['pcbnew'])
        # Exercise the unchanged shared runtime path using one tiny fake extension,
        # rather than modifying/querying the installed native binary.
        with tempfile.TemporaryDirectory(dir=HERE) as temp,ExitStack() as stack:
            extension=Path(temp)/'_pcbnew.so';extension.write_bytes(b'original library')
            p={'tools':{'pcbnew':{'path':str(extension),'bytes':64,'sha256':'prospective'}},'basis':{}}
            stack.enter_context(patch.object(driver.base,'head_witness',return_value={'head':'same'}))
            stack.enter_context(patch.object(driver,'source_paths',return_value=[]))
            stack.enter_context(patch.object(driver.original,'source_binding',return_value=({},0)))
            before=driver.runtime(p);extension.write_bytes(b'changed library');after=driver.runtime(p)
            self.assertNotEqual(before,after)
            self.assertNotEqual(before['tools']['pcbnew']['sha256'],after['tools']['pcbnew']['sha256'])
    def test_same_board_initialization_once_and_failure_retention(self):
        for success in (True,False):
            with self.subTest(success=success),tempfile.TemporaryDirectory(dir=HERE) as temp:
                report=Path(temp)/'init.txt';native=object();calls=[]
                class P:
                    EDA_UNITS_MM=1
                    @staticmethod
                    def WriteDRCReport(board,path,unit,all_errors):
                        calls.append((board,unit,all_errors));Path(path).write_text('actual-format placeholder only');return success
                cb=worker.callback(report)
                with patch.object(worker,'clearances',return_value=[]),patch.object(worker.original,'observe',return_value={'base':True}):
                    if success:
                        a=cb(native,P);b=cb(native,P);self.assertEqual(a,b)
                    else:
                        with self.assertRaises(ValueError):cb(native,P)
                self.assertEqual(calls,[(native,1,True)])
                saved=json.loads((Path(temp)/'clearance-initialization.json').read_text());self.assertEqual(saved['initialization_returned'],success)
                self.assertIn('pre_initialization',saved)
    def test_shared_publication_invalidates_late_material(self):
        for which in ('positive','evidence','cancel'):
            with self.subTest(which=which),tempfile.TemporaryDirectory(dir=HERE) as temp:
                out=Path(temp);material=out/'report';material.write_bytes(b'raw');expected=driver.inventory(out);n=[0]
                def stable():
                    n[0]+=1
                    if n[0]==2 and which=='evidence':material.write_bytes(b'changed')
                    if n[0]==2 and which=='cancel':raise KeyboardInterrupt('controlled cancellation')
                    actual=driver.inventory(out)
                    if any(actual.get(k)!=v for k,v in expected.items()):raise ValueError('evidence stale')
                record={'observations_complete':True,'routing_accepted':False}
                result=driver.base.publish(out,record,stable,lambda:None,lambda:1)
                self.assertEqual(result['observations_complete'],which=='positive')
                self.assertEqual(json.loads((out/'summary.json').read_text())['observations_complete'],which=='positive')
    def test_controller_keeps_all_stages_and_invalidates_final_mutations(self):
        """Real tiny files, mocked native/JVM commands only; no native qualification."""
        for variant in ('positive','source','raw-observation','helper','cancel','cap','capture-failure'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory(dir=HERE) as temp,ExitStack() as stack:
                root=Path(temp);here=root/'experiments/pic_mixed_transport_probe_v1';here.mkdir(parents=True)
                (root/'.runs').mkdir();source=root/'.data/pic_programmer.kicad_pcb';source.parent.mkdir()
                source.write_text('(kicad_pcb)');project=source.with_suffix('.kicad_pro');project.write_text('{}')
                helper=here/'driver.py';helper.write_text('fixed helper bytes')
                protocol=json.loads((HERE/'PROTOCOL.json').read_text());(here/'PROTOCOL.json').write_text(json.dumps(protocol))
                pin=lambda p:driver.base.content(p,digest=True)
                def runtime(p):return {'git':{'head':'1'*40},'sources':{str(helper.relative_to(root)):pin(helper)},
                    'tools':{k:{x:v[x] for x in ('bytes','sha256')} for k,v in protocol['tools'].items()},'basis':protocol['basis'],
                    'original':{p.name:pin(p)['sha256'] for p in (source,project)},'original_bytes':source.stat().st_size+project.stat().st_size}
                def git(argv,**kwargs):return SimpleNamespace(stdout=helper.read_bytes())
                synthetic=self.synthetic();out=root/'.runs/run';old_write=driver.base.write;late=[False]
                def write(path,value):
                    result=old_write(path,value)
                    if path==out/'summary.json' and value.get('observations_complete') and not late[0]:
                        late[0]=True
                        if variant=='source':source.write_text('(changed)')
                        if variant=='raw-observation':(out/'observations.json').write_text('{}')
                        if variant=='helper':helper.write_text('late changed helper')
                        if variant=='cancel':raise KeyboardInterrupt('controlled final publication signal')
                    return result
                def cpu():return 181 if late[0] and variant=='cap' else 0
                def run(argv,**kwargs):
                    log=kwargs['log'];log.write_text('mocked stage; no execution')
                    if log.name=='native-observe.log':(out/'native.dsn').write_text('mocked captured bytes')
                    if log.name=='native-observe.log' and variant=='capture-failure':(out/'code'/helper.relative_to(root)).write_text('changed copied helper')
                    if log.name=='compile.log':(out/'classes/Probe.class').write_bytes(b'mocked class')
                    if log.name=='import.log':(out/'observations.json').write_text(json.dumps(synthetic))
                    return {'status':'success','exit_code':0,'cleanup_complete':True,'pid':123,'argv':argv,'cwd':str(out)}
                for obj,name,value in [(driver,'ROOT',root),(driver,'HERE',here),(driver.original,'SOURCE',source),
                    (driver,'runtime',runtime),(driver.subprocess,'run',git),(driver.mapping,'source_notes',lambda *_:{}),
                    (driver,'verify_native',lambda *_:(self.derived,self.expected,{'initialized':True})),
                    (driver.runner,'run',run),(driver.base,'write',write),(driver.base,'cpu',cpu)]:stack.enter_context(patch.object(obj,name,value))
                result=driver.experiment(out)
                self.assertEqual(len(result['steps']),1 if variant=='capture-failure' else 3)
                self.assertTrue(result['native_process_executed'])
                self.assertEqual(result['import_process_executed'],variant!='capture-failure')
                self.assertEqual(result['observations_complete'],variant=='positive',result)
                self.assertEqual(json.loads((out/'summary.json').read_text())['observations_complete'],variant=='positive')
                self.assertTrue((out/'native.dsn').exists())
                self.assertTrue((out/('native-observe-process.json' if variant=='capture-failure' else 'import-process.json')).exists())
    def test_api_source_scope_is_import_only(self):
        java=(HERE/'MixedClassProbe.java').read_text()
        for required in ('manager.loadFromSpecctraDsn','board.awaitPostLoad()','new RoutingJob()','m.getValue(a,z,l,false)','nc.defaultItemClearanceClasses.get(ic)'):self.assertIn(required,java)
        for forbidden in ('new RoutingJobScheduler','new RoutingPipeline','SesWriter.write','changePlaneAsObstacle('):self.assertNotIn(forbidden,java)

if __name__=='__main__':unittest.main()
