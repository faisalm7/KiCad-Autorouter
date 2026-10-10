"""Read-only independent stored native fixture audit; never launches native jobs."""
from pathlib import Path
import collections,copy,hashlib,importlib,importlib.util,json,math,subprocess,sys,types
from decimal import Decimal
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'.runs/board-floor-forced-via-001';OUT=Path(__file__).resolve().parent
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
tools=summary['tools'];source=RUN/'source/fixture.kicad_pcb';hashes=summary['source_hashes']
need(not list(RUN.glob('invalidated-*-summary.json')),'fresh successful run has no invalidated positive summary')
need(summary['status']=='completed' and summary['controls_passed'] is True and 'error' not in summary,'fresh overall controls completed successfully')
need(all(summary[k] is False for k in ('routing_accepted','production_support_qualified','comparison_eligible','physical_electrical_validation')),'no production/routing/comparison claims')
need(summary['stage']=='forced-via' and summary['seconds_ceiling']==summary['cpu_seconds_ceiling']==120,'forced-via stage shared120 caps')
need(summary['original_inputs_unchanged'] is True,'recorded original-input guard passed')
need(tools['git_head']=='efc174e8ffda7796d56f663d87885b444c7bc729','exact fresh committed production freeze')
need(tree(source.parent)==hashes,'frozen original fixture exact')
need(tree(ROOT/'.runs/board-floor-native-draft-002/fixture')==hashes,'live original fixture exact')
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

need(len(summary['cases'])==1,'one forced-via actual case')
entry=summary['cases'][0];directory=RUN/'forced-via';board=directory/'candidate/fixture.kicad_pcb';candidate=sx.read(board)
need(entry==read(directory/'case.json') and entry['case']=='forced-via-engine' and entry['passed'] is True and entry['solver_executed'] is True and entry['zero_via_is_failure'] is True,'exact successful diagnostic receipt')
need(p.immutable(candidate)==base,'original native geometry/nets/pads/zones/rules unchanged')
digest=sha(board);inventory=dict(hashes);inventory[source.name]=digest
need(digest==entry['candidate_sha256'] and tree(board.parent)==inventory,'exact candidate and original project/rules inventory')

# The initial exported board was subsequently routed. Its exact original bytes
# are retained in source and initial context/native-input, not the final candidate.
initialctx=read(directory/'native-context.json')
need(initialctx['source']==str(board) and initialctx['board_sha256']==hashes[source.name] and initialctx['project_sha256']==hashes[source.with_suffix('.kicad_pro').name] and initialctx['dsn_sha256']==sha(directory/'native.dsn'),'original export exact source/project/raw-DSN binding')
need(initialctx['input_hashes_before']==initialctx['input_hashes_after']==hashes and initialctx['board_saved'] is False and initialctx['routes']==[],'initial native export immutable complete source input')
need(initialctx['floors_nm']==floors and initialctx['pads']==ctx['pads'] and initialctx['nets']==ctx['nets'] and g.qualify(project,initialctx,base)==qualified,'initial engine context original terminals/classes/floors')
process(directory,'native-context',[str(p.c.PYTHON),'-B',str(RUN/'code/native_context_worker.py'),str(board),str(directory/'native.dsn'),str(directory/'native-context.json')],0)
guided,guide_receipt=g.transform((directory/'native.dsn').read_bytes(),initialctx,source.with_suffix('.kicad_pro').read_bytes(),source.read_bytes())
need(guided==(directory/'floor-guided.dsn').read_bytes() and guide_receipt==read(directory/'guidance.json'),'exact raw-to-guided DSN transform and receipt')
need(guided==(directory/'task.dsn').read_bytes(),'both adapter is exact no-op on owned no-zone/no-copper-graphics fixture')
for filename,key in [('native.dsn','native_dsn_sha256'),('floor-guided.dsn','guided_dsn_sha256'),('task.dsn','task_dsn_sha256'),('routes.ses','ses_sha256')]:need(sha(directory/filename)==entry[key],'actual stage hash '+filename)
adapter=importlib.import_module('autorouter.adapter');dsn=adapter._parse_dsn((directory/'task.dsn').read_text());nets=adapter._network_summary(dsn)
need(entry['adapter']['mode']=='both' and entry['adapter']['classification']=='B1_adapter_only' and entry['adapter']['input_sha256']==entry['guided_dsn_sha256']==entry['adapter']['output_sha256'] and entry['adapter']['net_pin_mapping']==nets and entry['adapter']['net_pin_mapping_unchanged'] is True and entry['adapter']['transformations']==[],'correct adapter-only no-op receipt')
settings=entry['engine_settings'];remaining=settings['remaining_outer_wall_seconds_at_assignment']
need(type(remaining) in (int,float) and math.isfinite(remaining) and 40<remaining<=120,'engine nested within120 outer wall/CPU assignment')
need(p.engine_profile_settings('completion-only',remaining,strict_class_targets=True)==settings,'exact safe engine profile computed from remaining budget')
need(settings['assigned_job_timeout_seconds']==60 and settings['assigned_optimizer_timeout_seconds'] is None and settings['strict_class_targets'] is True,'completion-only60 engine with unchanged fixed route dimension policy')
argv=[str(p.c.JAVA),'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(p.c.JAR),'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(directory/'engine-config'),'--logging.file.enabled=false',*settings['argv'],'-de',str(directory/'task.dsn'),'-do',str(directory/'routes.ses')]
engine=process(directory,'engine',argv,0)
log=(directory/'engine.log').read_text();need('Freerouting v2.5.0' in log and 'finished with state: COMPLETED' in log and 'Successfully saved output file' in log and 'timed out' not in log.lower() and 'TIMED_OUT' not in log,'actual completed engine and SES output without timeout')
process(directory,'import',[str(p.c.PYTHON),'-B',str(RUN/'code/native.py'),'import',str(board),str(directory/'imported.kicad_pcb'),str(directory/'routes.ses')],0)
imported=sx.read(directory/'imported.kicad_pcb')
need(p.transplant_routes(base,imported)==candidate,'actual imported SES routes exactly transplanted into immutable source')
route_dimensions=g.audit_generated_routes(candidate,qualified)
need(route_dimensions['passed'] and route_dimensions['counts']=={'segment':7,'arc':0,'via':1},'all seven generated widths plus via copper/drill equal unchanged derived targets')

# Independently decode the actual SES transport scale, copper shapes, via name
# drill encoding, wire geometry and net labels; compare imported saved objects.
session=sx.read(directory/'routes.ses');routes=sx.one(session,'routes');resolution=sx.one(routes,'resolution')
need(session[0]=='session' and resolution==['resolution','um','10'],'actual SES coordinate resolution')
scale=Decimal(1000)/Decimal(resolution[2])
def ses_nm(value):
    v=Decimal(value)*scale
    if not v.is_finite() or v!=v.to_integral_value():raise ValueError('nonintegral SES coordinate')
    return int(v)
library=sx.one(routes,'library_out');pads=sx.children(library,'padstack')
need(len(pads)==1 and sx.unquote(pads[0][1])=='Via[0-1]_1500:300_um','SES selected via ID transports derived copper and original drill')
circles=[sx.one(shape,'circle') for shape in sx.children(pads[0],'shape')]
need(sorted((c[1],ses_nm(c[2]),ses_nm(c[3]),ses_nm(c[4])) for c in circles)==[('B.Cu',1500000,0,0),('F.Cu',1500000,0,0)],'SES actual via copper on both layers exactly1.5mm')
def seg_key(net,layer,width,a,b):return ('segment',net,layer,width,tuple(sorted((tuple(a),tuple(b)))))
expected=[]
for net in sx.children(sx.one(routes,'network_out'),'net'):
    netname=sx.unquote(net[1]);need(netname in {'SIGNAL_A','SIGNAL_B'},'SES net originally declared '+netname)
    for wire in sx.children(net,'wire'):
        path=sx.one(wire,'path');layer=path[1];width=ses_nm(path[2]);points=[(ses_nm(path[i]),-ses_nm(path[i+1])) for i in range(3,len(path),2)]
        need(width==300000 and layer in ('F.Cu','B.Cu') and len(points)>=2,'SES wire width/layer/vertices')
        expected.extend(seg_key(netname,layer,width,a,b) for a,b in zip(points,points[1:]))
    for via in sx.children(net,'via'):
        need(sx.unquote(via[1])=='Via[0-1]_1500:300_um','SES via instance correct library ID')
        expected.append(('via',netname,1500000,300000,(ses_nm(via[2]),-ses_nm(via[3])),('F.Cu','B.Cu')))
def board_route_keys(tree):
    keys=[]
    for route in p.routes(tree):
        net=sx.unquote(sx.one(route,'net')[1])
        if route[0]=='segment':keys.append(seg_key(net,sx.unquote(sx.one(route,'layer')[1]),nm(sx.one(route,'width')[1]),[nm(v) for v in sx.one(route,'start')[1:3]],[nm(v) for v in sx.one(route,'end')[1:3]]))
        elif route[0]=='via':keys.append(('via',net,nm(sx.one(route,'size')[1]),nm(sx.one(route,'drill')[1]),tuple(nm(v) for v in sx.one(route,'at')[1:3]),tuple(sx.unquote(v) for v in sx.one(route,'layers')[1:])))
        else:raise ValueError('unexpected imported arc')
    return collections.Counter(keys)
need(collections.Counter(expected)==board_route_keys(candidate)==board_route_keys(imported),'independent SES-to-import-to-final exact net geometry dimensions and drill')

native=p.parse_report(directory/'final-drc.json',source.name);raw=read(directory/'final-drc.json')
need(native==entry['native'] and p.native_accepted(native) and not raw['violations'] and not raw['unconnected_items'] and not raw['schematic_parity'],'actual original-rule native report has zero findings')
need(sha(directory/'final-drc.json')==entry['final_drc_sha256'] and sha(directory/'final-drc-binding.json')==entry['binding_sha256'],'final raw report and binding exact receipt hashes')
geometry=read(ROOT/'.runs/board-floor-geometry-002/summary.json')
need(native['ignored_checks']==geometry['cases'][0]['native']['ignored_checks'],'same original ignored-check set as fresh geometry positive')
need(geometry['source_hashes']==hashes and geometry['tools']==tools,'native geometry and engine/import qualifications share exact source/code/tools')
for stem,saved,subdir in [('refill-drc',True,'refill'),('final-drc',False,'final-drc-input')]:
    inp=directory/subdir/source.name;binding=read(directory/(stem+'-binding.json'))
    need(binding['input']==str(inp) and binding['source']==str(inp if saved else board) and binding['saved'] is saved,'exact native binding paths '+stem)
    need(binding['before']==inventory and tree(inp.parent)==binding['after'],'native actual input tree '+stem)
    need(all(binding['after'].get(k)==v for k,v in hashes.items() if k!=source.name) and set(binding['after'])-set(hashes)=={'fixture.kicad_prl'},'full original project rules unchanged '+stem)
    if not saved:need(binding['after'][source.name]==digest,'native report checked exact final candidate bytes')
    else:need(board_route_keys(sx.read(inp))==board_route_keys(candidate),'refill preserved all SES copper geometry')
    need(p.parse_report(directory/(stem+'.json'),source.name)==native,'refill and final actual native zero-finding report equality')
    argv=[str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/(stem+'.json'))]+(['--save-board'] if saved else [])+[str(inp)]
    step=process(directory,stem,argv,0);need(step['validated_input_sha256']==digest,'recorded exact DRC input hash '+stem)
finalctx=context(directory,'final',board)
need(g.qualify(project,finalctx,base)==qualified and finalctx['pads']==ctx['pads'] and finalctx['nets']==ctx['nets'],'fresh final native original pads/nets/classes/floors')
observed={v['uuid']:v for v in finalctx['routes']};need(len(observed)==len(finalctx['routes'])==8,'native route population and UUID uniqueness')
for route in p.routes(candidate):
    uid=sx.unquote(sx.one(route,'uuid')[1]);v=observed[uid]
    need(v['net']==sx.unquote(sx.one(route,'net')[1]) and v['kind']==route[0],'native route UUID/net/kind '+uid)
    if route[0]=='via':need(v['width_nm']==1500000 and v['drill_nm']==300000 and v['position_nm']==[nm(x) for x in sx.one(route,'at')[1:3]] and v['layers']==['F.Cu','B.Cu'],'actual native via imported copper/drill/position/layers')
    else:need(v['width_nm']==300000 and v['start_nm']==[nm(x) for x in sx.one(route,'start')[1:3]] and v['end_nm']==[nm(x) for x in sx.one(route,'end')[1:3]] and v['layer']==sx.unquote(sx.one(route,'layer')[1]),'actual native imported track width/placement '+uid)
vias=[v for v in finalctx['routes'] if v['kind']=='via'];need(len(vias)==entry['signal_vias']==1 and vias[0]['net']=='SIGNAL_A','nonzero native observed via on opposing-side source net')
need(entry['native_route_readback']=={'passed':True,'native_route_count':8,'native_via_count':1},'exact native readback counter receipt')
need(len(summary['steps'])==7,'all seven actual native/engine/import processes recorded once')
need(close(summary['child_cpu_seconds'],sum(s['cpu_seconds'] for s in summary['steps'])) and close(summary['monitor_cpu_seconds'],sum(s['monitor_cpu_seconds'] for s in summary['steps'])),'exact child/monitor CPU totals')
need(sum(s['wall_seconds'] for s in summary['steps'])<=summary['wall_seconds'] and summary['child_cpu_seconds']<=summary['total_cpu_seconds'],'whole-operation preparation and waited-child costs included')
need(summary['within_budget'] is True and 0<summary['wall_seconds']<120 and 0<summary['total_cpu_seconds']<120,'native diagnostic within120 wall/CPU caps')
need(tree(RUN)==initial,'entire actual run unchanged by review')
result={'passed':not failures,'checks':len(checks),'failures':failures,'native_executed_by_reviewer':False,'frozen_commit':tools['git_head'],'run_status':summary['status'],'controls_passed':summary['controls_passed'],'source_sha256':hashes[source.name],'original_project_sha256':hashes[source.with_suffix('.kicad_pro').name],'candidate_sha256':digest,'native_report_sha256':entry['final_drc_sha256'],'ses_sha256':entry['ses_sha256'],'native':native,'route_readback':entry['native_route_readback'],'independent_ses_geometry_and_drill_transport_verified':True,'native_vias':vias,'engine_wall_seconds':engine['wall_seconds'],'engine_cpu_seconds':engine['cpu_seconds'],'wall_seconds':summary['wall_seconds'],'total_cpu_seconds':summary['total_cpu_seconds'],'script_sha256':sha(__file__),'scope':['Real raw native export → original-floor guidance → existing adapter → Freerouting → SES import → refill → final native validation verified on the owned fixture.','Nonzero via1.5mm copper/.3mm drill transported via the selected padstack identity and measured by native readback.','No production integration/support, independent-family routing comparison, physical/electrical or human review claim.','Original source/project/rules/ignored checks unchanged.','Measured total CPU and wall are cooperative final caps, not hard OS aggregate quota; stored sample precedes final freshness/publication.','No reviewer native or engine jobs.']}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(bool(failures))
