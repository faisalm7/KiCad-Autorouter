"""Pure/synthetic contract controls; none launches Java, a router or KiCad."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import signal
import unittest
from unittest import mock

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/runner.py').is_file())
SCRIPT=Path(__file__).resolve().parents[1]/'scripts/probe_engine_profiles.py'
SPEC=importlib.util.spec_from_file_location('layer_probe_tested',SCRIPT)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
b=m.layer_helpers()


def observation():
    """Explicit synthetic outputs, not derived from the validator being tested."""
    rows=[]
    for name,mask in [('source-all',[True,True]),('front-only',[True,False]),('back-only',[False,True]),('reversed-mapping-negative',[False,True])]:
        argv=['--router.autorouter.enabled=false','--router.optimizer.enabled=false','--router.layers.routable='+','.join(str(v).lower() for v in mask)]
        board={'bounded':True,'layer_count':2,'pin_count':4,'trace_count':0,'via_count':0,'item_count':4,
            'layers':[{'index':0,'name':'F.Cu','signal':True},{'index':1,'name':'B.Cu','signal':True}],
            'items':[{'id':i,'class':'app.freerouting.board.model.items.Pin','first_layer':0,'last_layer':1,'nets':[1 if i<3 else 2]} for i in range(1,5)]}
        states=[{'name':stage,'settings_layer_count':2,'flags':[{'index':i,'raw_routable':v,'active':v} for i,v in enumerate(mask)],
            'autorouter_enabled':False,'optimizer_enabled':False,'ignored_netclasses':[],'board':copy.deepcopy(board)}
            for stage in ('before_init','after_init','after_if_needed')]
        rows.append({'case':name,'status':'observed','input_sha256':m.DSN_SHA,'argv':argv,
            'parser_result_class':'app.freerouting.io.BoardReadResult$Success','parser_warnings':[],
            'sources':[{'class':'app.freerouting.settings.sources.'+n,'name':n,'priority':i} for i,n in enumerate(('DefaultSettings','DsnFileSettings','CliSettings'))],
            'parsed_cli_arguments':dict(flag[2:].split('=',1) for flag in argv),'states':states})
    return {'schema':1,'mode':m.LAYER_MODE,'input_sha256':m.DSN_SHA,'routing_executed':False,'native_executed':False,'layer_support_qualified':False,'cases':rows}


class Layers(unittest.TestCase):
    def test_name_keyed_mask_order_and_strict_bad_inputs(self):
        self.assertEqual(m.build_layer_mask([('B.Cu',False),('F.Cu',True)]),[True,False])
        self.assertEqual(m.build_layer_mask([('F.Cu',True),('B.Cu',False)]),[True,False])
        for pairs in ([],[('F.Cu',True)],[('F.Cu',True)]*2,[('F.Cu',True),('X',False)],
                      [('F.Cu',1),('B.Cu',False)],[('F.Cu','true'),('B.Cu',False)],
                      [('F.Cu',None),('B.Cu',False)],[('F.Cu',True),('B.Cu',False),('X',True)]):
            with self.subTest(pairs=pairs),self.assertRaises(ValueError):m.build_layer_mask(pairs)
        with self.assertRaises(ValueError):m.build_layer_mask([('F.Cu',True),('B.Cu',False)],('B.Cu','F.Cu'))

    def test_four_cases_and_literal_reversed_negative(self):
        rows=m.validate_layer_observations(observation(),m.layer_request('/fixture.dsn'))
        self.assertEqual([r['semantic_mapping_accepted'] for r in rows],[True,True,True,False])
        self.assertEqual(rows[-1]['enabled_names'],['B.Cu'])
        self.assertEqual(rows[-1]['requested_names'],['F.Cu'])
        self.assertTrue(rows[-1]['expected_semantic_rejection'])

    def test_capture_contract_falsifiers(self):
        edits=[lambda a:a.update(schema=True),lambda a:a['cases'].pop(),lambda a:a['cases'].append(a['cases'][0]),
            lambda a:a['cases'][1].update(input_sha256='f'*64),lambda a:a['cases'][0]['sources'].pop(1),
            lambda a:a['cases'][0]['parsed_cli_arguments'].update({'router.layers.routable':'1,1'}),
            lambda a:a['cases'][0]['states'].pop(),lambda a:a['cases'][0]['states'][0].update(autorouter_enabled=True),
            lambda a:a['cases'][0]['states'][0].update(ignored_netclasses=['Default']),
            lambda a:a['cases'][0]['states'][0]['flags'][0].update(raw_routable=None),
            lambda a:a['cases'][0]['states'][1]['flags'][1].update(active=False),
            lambda a:a['cases'][0]['states'][2]['flags'][0].update(active=1),
            lambda a:a['cases'][0]['states'][0]['board']['layers'].reverse(),
            lambda a:a['cases'][0]['states'][0]['board']['layers'][0].update(name='In1.Cu'),
            lambda a:a['cases'][0]['states'][0]['board'].update(layer_count=3),
            lambda a:a['cases'][0]['states'][0]['board'].update(pin_count=True),
            lambda a:a['cases'][0]['states'][1]['board']['items'][0].update(nets=[2]),
            lambda a:a['cases'][0]['states'][0]['board']['items'][1].update(id=1)]
        for i,edit in enumerate(edits):
            with self.subTest(case=i):
                actual=observation();edit(actual)
                with self.assertRaises((ValueError,TypeError)):m.validate_layer_observations(actual,m.layer_request('/fixture.dsn'))

    def test_strict_duplicate_nonfinite_json(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}'):
            with self.assertRaises(ValueError):b.decode(raw)

    def test_exact_retained_dsn_and_basis(self):
        self.assertEqual(b.sha(b.content(ROOT/m.DSN_REL,65536)),m.DSN_SHA)
        for path,want in m.LAYER_BASIS.items():
            self.assertTrue(path.startswith('evidence/'), 'research basis must ship in a clean checkout')
            self.assertNotIn('.runs',Path(path).parts)
            self.assertEqual(b.sha(b.content(ROOT/path,1024**2)),want,path)

    def test_default_behavior_fragments_retained(self):
        # Source comparison only: Java execution remains a ROOT qualification.
        old=(ROOT/'scripts/EngineProfileProbe.java').read_text()
        new=SCRIPT.with_name('EngineProfileProbe.java').read_text()
        fragment=old[old.index('    Class<?> cliClass'):]
        self.assertIn(fragment,new)
        self.assertEqual(m.expected_setting('router.optimizer.improvement_threshold','0.001'),0.1)
        self.assertEqual(m.expected_setting('router.job_timeout','00:01:00'),'00:01:00')

    def test_whole_flow_capture_and_publication(self):
        # Real temporary files, fake run/git/tool callbacks; no external processes.
        import types
        variants=('positive','changed-dsn','changed-process','changed-observations','late-source','late-result','cancel','cap','SIGINT','SIGTERM')
        for variant in variants:
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();(root/'.runs').mkdir();(root/'scripts').mkdir();(root/'basis').mkdir()
                helper=root/'scripts/probe_engine_profiles.py';helper.write_bytes(b'fixture helper')
                dsn=root/'basis/fixture.dsn';dsn.write_bytes((ROOT/m.DSN_REL).read_bytes())
                out=root/'.runs/run';runtime={'sources':{'scripts/probe_engine_profiles.py':b.content(helper,digest=True)},
                    'tools':{'java':{'path':'/not-executed/java'},'freerouting':{'path':'/not-executed/jar'}},'basis':{},'git':{'head':'a'*40}}
                altered=[False];parsed=[False];published=[False]
                def material():
                    result=copy.deepcopy(runtime)
                    result['sources']['scripts/probe_engine_profiles.py']=b.content(helper,digest=True)
                    if parsed[0] and not altered[0] and variant.startswith('changed-'):
                        target={'changed-dsn':'fixture.dsn','changed-process':'process.json','changed-observations':'observations.json'}[variant]
                        with (out/target).open('ab') as f:f.write(b' ')
                        altered[0]=True
                    if published[0] and not altered[0] and variant=='late-source':
                        helper.write_bytes(b'changed');altered[0]=True
                        result['sources']['scripts/probe_engine_profiles.py']=b.content(helper,digest=True)
                    return result
                def worker(argv,**kw):
                    self.assertEqual(argv[-1],'--layer-mask')
                    self.assertIn('-Xmx256m',argv);self.assertIn('-XX:ActiveProcessorCount=1',argv)
                    self.assertEqual(argv[:3],b.SANDBOX)
                    self.assertEqual(kw['env']['HOME'],str(out/'home'))
                    self.assertEqual(kw['max_log_bytes'],1024**2)
                    self.assertEqual(kw['max_workdir_bytes'],10*1024**2)
                    kw['log'].write_bytes(b'fake import worker\n');(out/'observations.json').write_bytes(b.canonical(observation()))
                    return {'argv':argv,'status':'success','exit_code':0,'cleanup_complete':True,'log_truncated':False}
                validate=m.validate_layer_observations
                def parse(actual,request):
                    rows=validate(actual,request);parsed[0]=True;return rows
                write=b.write
                def publish(path,value):
                    raw=write(path,value)
                    if path.name=='result.json' and value.get('passed'):
                        published[0]=True
                        if variant=='cancel':raise KeyboardInterrupt('test after positive publication')
                        if variant in ('SIGINT','SIGTERM'):os.kill(os.getpid(),getattr(signal,variant))
                        if variant=='late-result':path.write_bytes(b'{}\n')
                    return raw
                def now():return 61 if variant=='cap' and published[0] else 0
                with mock.patch.object(m,'ROOT',root),mock.patch.object(m,'__file__',str(helper)),mock.patch.object(m,'DSN_REL','basis/fixture.dsn'),\
                     mock.patch.object(m,'layer_runtime',side_effect=material),mock.patch.object(m,'run',side_effect=worker),\
                     mock.patch.object(m,'validate_layer_observations',side_effect=parse),mock.patch.object(b,'write',side_effect=publish),\
                     mock.patch('subprocess.run',return_value=types.SimpleNamespace(stdout=b'fixture helper')),mock.patch('time.monotonic',side_effect=now),mock.patch.object(b,'cpu',return_value=0):
                    handlers={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
                    with b.cancellation():result=m.layer_experiment(out,started=0,cpu_started=0)
                    self.assertEqual(handlers,{s:signal.getsignal(s) for s in handlers})
                canonical=b.decode((out/'result.json').read_bytes())
                self.assertEqual(canonical['passed'],variant=='positive',variant)
                self.assertEqual(result['passed'],variant=='positive',variant)
                self.assertFalse(canonical['layer_support_qualified'])
                if variant!='positive':self.assertNotEqual(canonical['status'],'completed')
                if variant in ('cancel','cap','late-result','late-source','SIGINT','SIGTERM'):self.assertTrue(list(out.glob('invalidated-*')))

    def test_publication_returned_value_and_failed_correction(self):
        for variant in ('mutated-return','correction-fails'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();record={'passed':True,'status':'completed'};calls=[0]
                def stable():
                    calls[0]+=1
                    if calls[0]==2:
                        if variant=='mutated-return':record['passed']=False
                        else:raise ValueError('stale')
                original=b.write;writes=[0]
                def writer(path,data):
                    writes[0]+=1
                    if writes[0]==2:raise OSError('correction fails')
                    return original(path,data)
                with mock.patch.object(b,'write',side_effect=writer):m.layer_publish(out,record,stable,lambda:None,lambda:1)
                self.assertFalse((out/'result.json').exists())
                self.assertTrue(list(out.glob('invalidated-*')))

    def test_runtime_samples_head_before_material(self):
        # Real content reads: emulate mutation at the last owned HEAD-read boundary.
        # This is distinct from whole-flow tests which replace layer_runtime itself.
        from contextlib import ExitStack
        for variant in ('positive','helper','basis','python','dsn'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
                root=Path(temp).resolve();(root/'tools').mkdir()
                for name in ('java','jar','python','sandbox'):(root/'tools'/name).write_text(name)
                for name in ('helper','basis','dsn'):(root/name).write_text(name)
                toolpins={name:{'path':'tools/'+file,**b.content(root/'tools'/file,digest=True)}
                          for name,file in (('java','java'),('freerouting','jar'))}
                (root/'toolchain.lock.json').write_bytes(b.canonical({'tools':toolpins}))
                pins={name:b.sha((root/name).read_bytes()) for name in ('basis','dsn')}
                original=b.content;calls=[0];target=root/('tools/python' if variant=='python' else variant)
                def content(path,*args,**kw):
                    path=root/'tools/sandbox' if Path(path)==Path('/usr/bin/sandbox-exec') else path
                    return original(path,*args,**kw)
                def head():
                    calls[0]+=1
                    if calls[0]==2 and variant!='positive':target.write_bytes(b'changed at HEAD boundary')
                    return {'head':'a'*40}
                with ExitStack() as stack:
                    for owner,name,value in ((m,'ROOT',root),(m,'LAYER_BASIS',pins),(m,'layer_source_paths',lambda:[root/'helper']),
                        (m.c,'resolve_tool_path',lambda v:root/v),(m.c,'JAR_SHA256',toolpins['freerouting']['sha256']),
                        (m.sys,'executable',str(root/'tools/python')),(b,'content',content),(b,'head_witness',head)):
                        stack.enter_context(mock.patch.object(owner,name,value))
                    before=m.layer_runtime()
                    try:changed=m.layer_runtime()!=before
                    except ValueError:changed=True
                self.assertEqual(changed,variant!='positive')


if __name__=='__main__':unittest.main()
