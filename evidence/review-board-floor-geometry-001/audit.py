"""Read-only independent stored native fixture audit; never launches native jobs."""
from pathlib import Path
import collections,copy,hashlib,importlib,importlib.util,json,math,subprocess,sys,types
from decimal import Decimal
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'.runs/board-floor-geometry-001';OUT=Path(__file__).resolve().parent
checks=[];failures=[]
def need(ok,label):
    checks.append(label)
    if not ok:failures.append(label)
def read(path):return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def tree(root):
    root=Path(root);need(root.is_dir() and not root.is_symlink(),'real directory '+str(root))
    rows={}
    for path in sorted(root.rglob('*')):
        need(not path.is_symlink(),'not symlink '+str(path))
        if path.is_file():rows[path.relative_to(root).as_posix()]=sha(path)
    return rows
def close(a,b):return abs(a-b)<1e-7
def nm(v):
    value=Decimal(v)*1000000
    if not value.is_finite() or value!=value.to_integral_value():raise ValueError('not integer nm')
    return int(value)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

initial=tree(RUN);summary=read(RUN/'summary.json')
old_paths=list(RUN.glob('invalidated-*-summary.json'));need(len(old_paths)==1,'one retained invalidated positive summary')
old=read(old_paths[0]);tools=summary['tools'];source=RUN/'source/fixture.kicad_pcb';hashes=summary['source_hashes']
need(summary['status']=='invalidated' and summary['controls_passed'] is False and summary['error']=='Rejected: summary changed','canonical run invalidated honestly')
need(old['status']=='completed' and old['controls_passed'] is True,'discarded positive summary retained')
need(all(summary[k] is False for k in ('routing_accepted','production_support_qualified','comparison_eligible','physical_electrical_validation')),'no production/routing/comparison claims')
need(summary['stage']=='geometry' and summary['seconds_ceiling']==summary['cpu_seconds_ceiling']==60,'geometry stage shared60 caps')
need({k:v for k,v in old.items() if k not in ('status','controls_passed','wall_seconds','total_cpu_seconds')}=={k:v for k,v in summary.items() if k not in ('status','controls_passed','wall_seconds','total_cpu_seconds','error')},'only status/error/accounting changed on invalidation')
need(tree(source.parent)==hashes,'frozen original fixture exact')
need(tree(ROOT/'.runs/board-floor-native-draft-001/fixture')==hashes,'live original fixture exact')
for path,digest in summary['original_inputs'].items():need(sha(path)==digest,'original input hash '+Path(path).name)
for path,digest in tools['files'].items():need(sha(path)==digest,'actual pinned tool hash '+Path(path).name)
for relative,digest in tools['implementation_sha256'].items():
    need(sha(RUN/'code'/Path(relative).name)==digest,'frozen production code '+relative)
    blob=subprocess.run(['git','-C',str(ROOT),'show',tools['git_head']+':'+relative],capture_output=True,check=True).stdout
    need(hashlib.sha256(blob).hexdigest()==digest,'production Git blob '+relative)
for path,digest in summary['original_inputs'].items():
    if Path(path).suffix=='.py':need(sha(RUN/'code'/Path(path).name)==digest,'frozen helper '+Path(path).name)
expected_code={Path(n).name for n in tools['implementation_sha256']}|{'driver.py','fixture_recipe.py','board_floor_guidance.py','native_context_worker.py'}
need(set(tree(RUN/'code'))==expected_code,'exact frozen helper/production file population')
for name,inventory in summary['completed_evidence'].items():need(tree(name)==inventory,'complete native evidence inventory '+Path(name).name)

# Import the retained source bytes, never the native worker or installed pcbnew.
pkg=types.ModuleType('autorouter');pkg.__path__=[str(RUN/'code')];sys.modules['autorouter']=pkg
p=importlib.import_module('autorouter.pipeline');sx=p.sx;p.c.ROOT=ROOT;p.c.JAR=ROOT/'.tools/freerouting-2.5.0.jar'
g=module('board_floor_guidance',RUN/'code/board_floor_guidance.py')
f=module('fixture_recipe',RUN/'code/fixture_recipe.py')
base=sx.read(source);project=read(source.with_suffix('.kicad_pro'))
need(p.immutable(base)==base and not p.routes(base) and not sx.children(base,'zone'),'source has no conductive layer bridge or routes/zones')
need(f.original(sx.read(ROOT/'fixtures/smoke/smoke.kicad_pcb'))==base,'original fixture recipe exactly reproduced')
need(f.force_via_topology(base)==summary['fixture_topology'],'opposite-side SMD premise unchanged')
need(not list(source.parent.glob('*.kicad_dru')) and not (ROOT/'.data/boards/kicad-multichannel/multichannel_mixer.kicad_dru').exists(),'no original custom rule file omitted')
rules=project['board']['design_settings']['rules']
floors={name:nm(str(rules[name])) for name in ('min_track_width','min_clearance','min_via_diameter','min_through_hole_diameter','min_via_annular_width')}
need(floors==dict(min_track_width=300000,min_clearance=300000,min_via_diameter=1500000,min_through_hole_diameter=300000,min_via_annular_width=300000),'unchanged original native minima')
ctx=read(RUN/'context/native-context.json');qualified=g.qualify(project,ctx,base)
need(qualified['derived_nm']==dict(width_nm=300000,clearance_nm=300000,via_diameter_nm=1500000,via_drill_nm=300000),'conservative derived targets')
encoded,receipt=g.transform((RUN/'context/native.dsn').read_bytes(),ctx,source.with_suffix('.kicad_pro').read_bytes(),source.read_bytes())
need(encoded==(RUN/'context/floor-guided.dsn').read_bytes() and receipt==read(RUN/'context/guidance.json'),'exact guided DSN transform and receipt reproduced')

prefix=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)']
def process(directory,name,argv,exit_code):
    raw=read(directory/(name+'-process.json'));steps=[s for s in summary['steps'] if s['name']==name and s['cwd']==str(directory)]
    need(len(steps)==1,'exact single process registration '+directory.name+'/'+name)
    step=steps[0]
    need(all(step.get(k)==v for k,v in raw.items()),'retained process equality '+directory.name+'/'+name)
    need(raw['argv']==prefix+argv and raw['cwd']==str(directory),'exact network-denied command '+directory.name+'/'+name)
    need(raw['exit_code']==exit_code and raw['status']==('success' if exit_code==0 else 'nonzero_exit'),'native process exit '+directory.name+'/'+name)
    need(raw['cleanup_complete'] and not raw['log_truncated'] and raw['log']==str(directory/(name+'.log')) and Path(raw['log']).stat().st_size==raw['log_bytes'],'process cleanup and full log '+directory.name+'/'+name)
    need(all(type(raw[k]) in (int,float) and math.isfinite(raw[k]) and raw[k]>=0 for k in ('wall_seconds','cpu_seconds','max_rss_bytes')),'finite process resources '+directory.name+'/'+name)
    return step
def context(directory,stem,board):
    data=read(directory/(stem+'-context.json'));inventory=tree(board.parent);dsn=directory/(stem+'.dsn')
    need(data['source']==str(board) and data['board_sha256']==sha(board) and data['project_sha256']==hashes['fixture.kicad_pro'] and data['dsn_sha256']==sha(dsn),'native context board/project/DSN binding '+directory.name)
    need(data['input_hashes_before']==data['input_hashes_after']==inventory and data['board_saved'] is False,'native context input immutability '+directory.name)
    need(data['native_version']=='10.0.0' and data['floors_nm']==floors,'actual native floors '+directory.name)
    process(directory,stem+'-context',[str(p.c.PYTHON),'-B',str(RUN/'code/native_context_worker.py'),str(board),str(dsn),str(directory/(stem+'-context.json'))],0)
    return data
context(RUN/'context','native',RUN/'context/native-input/fixture.kicad_pcb')

outcomes=[];ignored=None;tuples=[]
expected_counts={'positive':(0,0),'track_width':(1,1),'clearance':(3,0),'via_diameter':(2,0),'drill':(1,0),'annulus':(1,0)}
need([x['case'] for x in summary['cases']]==list(f.CASES),'all six expected actual cases in order')
for entry in summary['cases']:
    name=entry['case'];directory=RUN/('geometry-'+name);board=directory/'candidate/fixture.kicad_pcb';candidate=sx.read(board)
    recipe,expected=f.candidate(base,name);expected_json=json.loads(json.dumps(expected))
    need(entry==read(directory/'case.json'),'case receipt equals summary '+name)
    need(candidate==recipe and p.immutable(candidate)==base and entry['changed_routes_only'] is True,'exact prepared recipe and source invariants '+name)
    digest=sha(board);inventory=dict(hashes);inventory[source.name]=digest
    need(entry['prepared_candidate_sha256']==entry['candidate_sha256']==digest and tree(board.parent)==inventory,'candidate/source/rule hash equality '+name)
    need(entry['expected']==expected_json,'exact intended UUID error target '+name)
    if isinstance(expected,tuple):tuples.append('cases.'+str(len(outcomes))+'.expected')
    raw=read(directory/'final-drc.json');native=p.parse_report(directory/'final-drc.json',source.name)
    need(native==entry['native'] and sha(directory/'final-drc.json')==entry['final_drc_sha256'] and sha(directory/'final-drc-binding.json')==entry['binding_sha256'],'raw report/hash bound to receipt '+name)
    need(raw['source']==source.name and raw['kicad_version']=='10.0.0' and raw['coordinate_units']=='mm' and set(raw['included_severities'])=={'error','warning','exclusion'},'actual all-severity native report '+name)
    own_errors=[v for v in raw['violations'] if v['severity']=='error'];own_warnings=[v for v in raw['violations'] if v['severity']=='warning']
    need(not raw['unconnected_items'] and not raw['schematic_parity'] and not any(v.get('excluded') or v['severity']=='exclusion' for v in raw['violations']),'zero native opens/exclusions '+name)
    need((len(own_errors),len(own_warnings))==expected_counts[name] and native['blocking']==len(own_errors) and native['warnings']==len(own_warnings),'independent raw finding counts '+name)
    if ignored is None:ignored=native['ignored_checks']
    need(native['ignored_checks']==ignored,'identical original ignored checks '+name)
    configured=project['board']['design_settings']['rule_severities']
    need(all(configured.get(x['key'],'ignore')=='ignore' for x in ignored),'ignored checks not newly suppressed '+name)
    if expected:
        kind,ids=expected
        hits=[v for v in own_errors if v['type']==kind and set(ids)<={i['uuid'] for i in v['items']}]
        need(bool(hits) and hits==entry['targeted_native_findings'] and not p.native_accepted(native),'exact native negative UUID predicate '+name)
    else:need(not raw['violations'] and p.native_accepted(native),'native positive zero-finding predicate')
    for stem,saved,subdir in [('refill-drc',True,'refill'),('final-drc',False,'final-drc-input')]:
        inp=directory/subdir/source.name;binding=read(directory/(stem+'-binding.json'))
        need(binding['input']==str(inp) and binding['source']==str(inp if saved else board) and binding['saved'] is saved,'native binding paths '+name+'/'+stem)
        need(binding['before']==inventory and tree(inp.parent)==binding['after'],'native input full inventory '+name+'/'+stem)
        need(all(binding['after'].get(k)==v for k,v in hashes.items() if k!=source.name) and set(binding['after'])-set(hashes)=={'fixture.kicad_prl'},'original project/license files intact '+name+'/'+stem)
        if not saved:need(binding['after'][source.name]==digest,'final DRC exact candidate bytes '+name)
        argv=[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/(stem+'.json'))]+(['--save-board'] if saved else [])+[str(inp)]
        n=p.parse_report(directory/(stem+'.json'),source.name)
        finding_key=lambda v:(v['type'],v['severity'],v['description'],tuple(sorted(i['uuid'] for i in v['items'])))
        need({k:v for k,v in n.items() if k!='findings'}=={k:v for k,v in native.items() if k!='findings'} and sorted(map(finding_key,n['findings']))==sorted(map(finding_key,native['findings'])),'refill/final native finding types/descriptions/UUIDs match '+name+'/'+stem)
        step=process(directory,stem,argv,0 if name=='positive' else 5)
        need(step['validated_input_sha256']==digest,'process validated candidate SHA '+name+'/'+stem)
    finalctx=context(directory,'final',board)
    need(g.qualify(project,finalctx,base)==qualified and finalctx['pads']==ctx['pads'] and finalctx['nets']==ctx['nets'],'fresh final native pads/nets/classes/floors unchanged '+name)
    routes=p.routes(candidate);need(len(routes)==8 and len(finalctx['routes'])==8,'seven tracks one via '+name)
    observed={v['uuid']:v for v in finalctx['routes']};need(len(observed)==8,'native route UUID uniqueness '+name)
    for route in routes:
        uid=sx.unquote(sx.one(route,'uuid')[1]);v=observed[uid]
        need(v['net']==sx.unquote(sx.one(route,'net')[1]) and v['kind']==route[0],'native route identity '+name+'/'+uid)
        if route[0]=='via':
            need(v['width_nm']==nm(sx.one(route,'size')[1]) and v['drill_nm']==nm(sx.one(route,'drill')[1]) and v['position_nm']==[nm(x) for x in sx.one(route,'at')[1:3]] and v['layers']==['F.Cu','B.Cu'] and not any(x in route for x in ('blind','micro')),'native physical via copper/drill/layers '+name)
        else:need(v['width_nm']==nm(sx.one(route,'width')[1]) and v['start_nm']==[nm(x) for x in sx.one(route,'start')[1:3]] and v['end_nm']==[nm(x) for x in sx.one(route,'end')[1:3]] and v['layer']==sx.unquote(sx.one(route,'layer')[1]),'native track dimension/placement '+name+'/'+uid)
    try:
        dimensions=g.audit_generated_routes(candidate,qualified);dimension_valid=True
    except ValueError:dimension_valid=False
    need(dimension_valid==(name in ('positive','clearance')),'independent generated target dimension predicate '+name)
    need(entry['passed'] is True,'executed native control predicate recorded '+name)
    outcomes.append({'case':name,'native_control_predicate_verified':True,'routing_accepted':False,'candidate_sha256':digest,'report_sha256':sha(directory/'final-drc.json'),'opens':native['opens'],'blocking':native['blocking'],'warnings':native['warnings'],'exclusions':native['exclusions'],'finding_types':dict(collections.Counter(x['type'] for x in native['findings']))})

need(len(summary['steps'])==19,'one initial context plus six times refill/final/context')
need(close(summary['child_cpu_seconds'],sum(s['cpu_seconds'] for s in summary['steps'])) and close(summary['monitor_cpu_seconds'],sum(s['monitor_cpu_seconds'] for s in summary['steps'])),'exact child and monitor sums')
need(sum(s['wall_seconds'] for s in summary['steps'])<=summary['wall_seconds'] and summary['child_cpu_seconds']<=summary['total_cpu_seconds'],'parent preparation and sequential process budgets contained')
need(summary['within_budget'] is True and 0<summary['wall_seconds']<60 and 0<summary['total_cpu_seconds']<60,'invalidated observed totals within60 caps')

# Minimal pure reproduction of real publish bug, using its actual retained code.
driver=module('frozen_floor_driver_review',RUN/'code/driver.py')
record=copy.deepcopy(old)
for entry in record['cases']:entry['expected']=f.candidate(base,entry['case'])[1]
roundtrip=json.loads(json.dumps(record));need(record!=roundtrip,'actual record fails JSON identity due to tuple/list')
need(roundtrip==old,'all reconstructed differences are expected tuple/list fields')
index=1
while (OUT/('publication-reproduction-'+str(index).zfill(3))).exists():index+=1
scratch=OUT/('publication-reproduction-'+str(index).zfill(3));scratch.mkdir()
driver.publish(scratch,record,lambda:None,lambda:None)
need(read(scratch/'summary.json')['status']=='invalidated' and read(scratch/'summary.json')['controls_passed'] is False and read(scratch/'summary.json')['error']=='Rejected: summary changed','actual pure publication failure reproduced')
need(len(list(scratch.glob('invalidated-*-summary.json')))==1,'pure failing positive summary preserved')
need(tree(RUN)==initial,'all actual run evidence unchanged by review')
result={'passed':not failures,'checks':len(checks),'failures':failures,'native_executed_by_reviewer':False,'frozen_commit':tools['git_head'],'run_status':'invalidated','overall_controls_passed':False,'six_executed_case_predicates_verified':all(x['native_control_predicate_verified'] for x in outcomes),'cases':outcomes,'source_sha256':hashes[source.name],'original_project_sha256':hashes[source.with_suffix('.kicad_pro').name],'original_ignored_checks':ignored,'publication_failure':{'cause':'negative case expected tuple becomes list in JSON roundtrip','tuple_paths':tuples,'actual_frozen_publish_reproduced':True,'actual_run_unchanged':True},'wall_seconds':summary['wall_seconds'],'total_cpu_seconds':summary['total_cpu_seconds'],'script_sha256':sha(__file__),'scope':['Six actual native case predicates verified; overall run remains invalidated.','No engine or SES import ran; forced-via transport and production integration remain unqualified.','Original rules/geometry were unchanged; secondary warning/error findings retained.','Stored invalidated totals are a pre-publication sample; no accepted budget claim made.','No reviewer native jobs; frozen driver reproduction uses only JSON publication.']}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(bool(failures))
