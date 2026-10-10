"""Independent bounded saved-evidence audit only; no native, engine or network."""
import ast, hashlib, json, math, subprocess, sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,adapter
OBS=ROOT/'.runs/pic-custom-observation-002'
checks=[]
def ck(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
def raw(path,limit=32*1024*1024):
    assert not path.is_symlink() and path.stat().st_size<=limit
    with path.open('rb') as f:b=f.read(limit+1)
    assert len(b)<=limit;return b
def sha(path):
    assert not path.is_symlink();h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(path):return json.loads(raw(path),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def inv(root):
    out={};total=0;entries=0
    for x in root.rglob('*'):
        entries+=1;assert entries<=2048 and not x.is_symlink()
        if x.is_file():
            total+=x.stat().st_size;assert total<=32*1024*1024 and len(out)<512
            out[str(x.relative_to(root))]=sha(x)
    return dict(sorted(out.items()))
pre={str(OBS):inv(OBS)}
s=read(OBS/'summary.json');execution=read(ROOT/'.runs/pic-custom-observation-002-execution.json')
ck('run and outer execution HEADs same',s['tools']['git_head']==execution['git_head']=='129dde00902ea4aa775e9827db5a6def976e7384')
for key in ('routing_accepted','geometry_qualified','dependency_complete','format_support_qualified','board_saved','semantic_migration_performed','new_engine_execution'):
    ck('unqualified scope '+key,s[key] is False)
ck('successful observation scope honest',s['status']=='observations_complete' and s['observations_complete'] is True and 'error' not in s)
ck('correspondence and census separately observed',s['correspondence_verified'] is True and s['native_original_pad_route_identities_match'] is True and s['dsn_export_succeeded'] is True)
source=Path(s['source']);source_before=inv(source.parent);ck('all15 source inventory exact',source_before==s['source_hashes'] and len(source_before)==15)
ck('copy source inventory exact',inv(OBS/'observe-input')==source_before)
ck('source bytes exact',sum((source.parent/x).stat().st_size for x in source_before)==s['source_bytes']==1366598)
acq=read(ROOT/'data/sources.json');ck('acquisition receipt hash',sha(ROOT/'data/sources.json')==s['acquisition_receipt_sha256']);rows=[x for x in acq['files'] if x.get('project_id')=='kicad-pic-programmer']
ck('acquisition source commit/count',acq['commit']=='69cafb907ebc09e7722a2a464b1d466fc2e3608d' and len(rows)==15)
for x in rows:
    file=ROOT/'.data'/x['destination'];b=raw(file)
    ck('acquired blob '+str(file.relative_to(source.parent)),len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['git_blob_sha1'])
ck('exact runtime/snapshot key sets',s['runtime_sources']==s['code_inventory']==inv(OBS/'code'))
for name,digest in s['runtime_sources'].items():
    b=subprocess.run(['git','show',s['tools']['git_head']+':'+name],cwd=ROOT,capture_output=True,check=True,timeout=3).stdout
    ck('committed runtime '+name,hashlib.sha256(b).hexdigest()==digest and sha(ROOT/name)==digest)
for name,digest in s['tools']['files'].items():ck('installed pin '+name,sha(Path(name))==digest)
wrapper=ROOT # replaced with exact fixed wrapper path below
wrapper=Path('/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/pcbnew.py')
ck('installed wrapper pin',sha(wrapper)==s['native_wrapper_sha256'])
for name,digest in s['stage_one_evidence'].items():ck('stage frozen '+name,sha(OBS/name)==digest)
ck('stage-one file census',set(s['stage_one_evidence'])=={'observation.json','custom-pads.json','native.dsn','observe.log','observe-process.json'})
step=read(OBS/'observe-process.json');ck('exact one step and actual0exit',s['steps'][0]==step and [x['name'] for x in s['steps']]==['observe','original-drc'] and step['name']=='observe' and step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] is True)
ck('native exact argv',step['argv']==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(wrapper.parents[3]/'bin/python3.9'),str(ROOT/'experiments/pic_custom_observer_v1/worker.py'),str(OBS/'observe-input'/source.name),str(OBS/'observation.json'),str(OBS/'native.dsn'),str(OBS/'custom-pads.json')])
ck('native cwd/log',step['cwd']==str(OBS) and step['log']==str(OBS/'observe.log') and step['log_bytes']==len(raw(OBS/'observe.log')) and step['log_truncated'] is False)
ck('native resource guard params',step['resource_guards']['max_group_rss_bytes']==2*1024**3 and step['resource_guards']['max_workdir_bytes']==20*1024**2)
ck('native observed process fits',step['wall_seconds']<=s['wall_seconds'] and step['cpu_seconds']<=s['total_cpu_seconds'] and step['max_rss_bytes']<2*1024**3)
ck('stored sample within caps',s['within_budget'] is True and 0<=s['wall_seconds']<=60 and 0<=s['total_cpu_seconds']<=60 and s['budget_seconds']==s['cpu_budget_seconds']==60)
ck('current output fits20MiB',sum((OBS/x).stat().st_size for x in pre[str(OBS)])<20*1024**2)
ck('two complete input copies planned',len([x for x in OBS.iterdir() if x.is_dir() and x.name.endswith('-input')])==2 and s['planned_project_copy_bytes']==2*s['source_bytes'])
o=read(OBS/'observation.json');c=read(OBS/'custom-pads.json');before=c['observation_before_export'];ck('same native before/after observations',before==c['observation_after_export'] and c['same_loaded_board'] is True)
for key in ('context_schema','native_version','units','mode','source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after'):
    ck('custom/floor '+key,c[key]==o[key])
ck('worker input/output bindings',o['source']==str(OBS/'observe-input'/source.name) and o['board_sha256']==sha(source) and o['project_sha256']==sha(source.with_suffix('.kicad_pro')) and o['dsn_sha256']==sha(OBS/'native.dsn')==s['native_dsn_sha256'] and c['floor_context_sha256']==sha(OBS/'observation.json') and o['input_hashes_before']==o['input_hashes_after']==source_before)
ck('native no save no acceptance',o['board_saved'] is False and o['routing_accepted'] is False and c['geometry_qualified'] is False)
ck('native floor/schema',o['context_schema']==1 and o['native_version']=='10.0.0' and o['units']=='integer nanometres' and o['mode']=='export')
ck('full callback census',len(before['all_terminals'])==len(o['pads'])==before['total_pad_count']==247 and len(before['all_footprints'])==63 and len(before['pads'])==2)
board=sx.read(source);fps=sx.children(board,'footprint');pads={sx.unquote(sx.one(pad,'uuid')[1]):(fp,pad) for fp in fps for pad in sx.children(fp,'pad')}
fpids={sx.unquote(sx.one(fp,'uuid')[1]) for fp in fps}
ck('native footprint identity census',{x['uuid'] for x in before['all_footprints']}==fpids)
actual={x['uuid']:x for x in o['pads']};ck('native all247 pad identity census',set(actual)==set(pads) and len(actual)==247)
for uid,(fp,pad) in pads.items():
    ref=next(sx.unquote(x[2]) for x in sx.children(fp,'property') if sx.unquote(x[1])=='Reference')
    net=sx.one(pad,'net');name=sx.unquote(net[-1]) if net else ''
    ck('original pad terminal '+uid,actual[uid]['reference']==ref and actual[uid]['number']==sx.unquote(pad[1]) and actual[uid]['net']==name)
ck('callback full terminal identity',{x['uuid']:(x['reference'],x['number'],x['net'],x['netcode'],x['position_nm'],x['copper_layers']) for x in before['all_terminals']}=={x['uuid']:(x['reference'],x['number'],x['net'],x['netcode'],x['position_nm'],x['copper_layers']) for x in o['pads']})
ck('all original376 route UUIDs',{x['uuid'] for x in o['routes']}=={sx.unquote(sx.one(x,'uuid')[1]) for x in p.routes(board)} and len(o['routes'])==376)
nm=lambda x:int(Decimal(x)*1000000)
def canonical_polygon(pts):
    p=[tuple(x) for x in pts];return min(tuple(p[i:]+p[:i]) for p in (p,list(reversed(p))) for i in range(len(p)))
custom_rows=[]
for row in before['pads']:
    fp,pad=pads[row['uuid']];primitive=sx.one(sx.one(pad,'primitives'),'gr_poly');pts=[[nm(x[1]),nm(x[2])] for x in sx.children(sx.one(primitive,'pts'),'xy')]
    local=row['merged_local']['outlines'][0]['outline']['points_nm'];world=row['transformed_world']['outlines'][0]['outline']['points_nm'];effective=row['effective_world']['outlines'][0]['outline']['points_nm']
    ck('custom local source equality '+row['uuid'],canonical_polygon(local)==canonical_polygon(pts))
    ck('custom exact translated world '+row['uuid'],row['orientation_degrees']==0 and canonical_polygon(world)==canonical_polygon([[a+row['position_nm'][0],b+row['position_nm'][1]] for a,b in local]) and world==effective)
    ck('custom narrow shapes/layer '+row['uuid'],row['copper_layers']==['B.Cu'] and row['size_nm']==[300000,300000] and row['offset_nm']==row['drill_nm']==[0,0] and row['shape']=='custom' and row['anchor']=='rect' and row['pad_flipped'] is True)
    for key in ('merged_local','transformed_world','effective_world'):
        q=row[key];ck('polygon topology '+row['uuid']+key,q['arc_count']==0 and q['total_vertices']==5 and len(q['outlines'])==1 and q['outlines'][0]['holes']==[] and q['outlines'][0]['outline']['closed'] is True)
    custom_rows.append({'uuid':row['uuid'],'native_net':row['net'],'world_polygon_nm':world})
# The source implementation demonstrates one object and an explicit callback on both sides of export.
fc=ast.parse(raw(OBS/'code/autorouter/floor_context.py'));calls=[x for x in ast.walk(fc) if isinstance(x,ast.Call)]
ck('one load and export call source',sum(isinstance(x.func,ast.Attribute) and x.func.attr=='LoadBoard' for x in calls)==1 and sum(isinstance(x.func,ast.Attribute) and x.func.attr=='ExportSpecctraDSN' for x in calls)==1)
worker=raw(OBS/'code/experiments/pic_custom_observer_v1/worker.py').decode();ck('three declared explicit-layer APIs source',all(x in worker for x in ('MergePrimitivesAsPolygon(layer,merged','TransformShapeToPolygon(world,layer','GetEffectivePolygon(layer,')))
rawdsn=raw(OBS/'native.dsn').decode()
tree=adapter._parse_dsn(rawdsn);adapter._check_units(tree)
netnodes=sx.children(sx.one(tree,'network'),'net');nets={};tokens={}
for net in netnodes:
    name=sx.unquote(net[1]);ck('DSN unique net '+name,name not in nets);nets[name]=net
    for token in sx.one(net,'pins')[1:]:
        token=sx.unquote(token);ck('DSN unique terminal '+token,token not in tokens);tokens[token]=name
expected={x['reference']+'-'+x['number']:x['net'] for x in o['pads'] if x['netcode']>0 and x['copper_layers']}
ck('offline DSN-aware terminal census equals saved native',tokens==expected)
library=sx.one(tree,'library');images={sx.unquote(x[1]):x for x in sx.children(library,'image')};stacks={sx.unquote(x[1]):x for x in sx.children(library,'padstack')}
placements=[(comp,place) for comp in sx.children(sx.one(tree,'placement'),'component') for place in sx.children(comp,'place') if sx.unquote(place[1])=='JP1'];ck('one JP1 DSN placement',len(placements)==1)
comp,place=placements[0];image=images[sx.unquote(comp[1])];custom_dsn=[]
for row in before['pads']:
    pins=[x for x in sx.children(image,'pin') if sx.unquote([a for a in x[2:] if isinstance(a,str)][0])==row['number']];ck('one custom DSN pin '+row['number'],len(pins)==1)
    pin=pins[0];stack=stacks[sx.unquote(pin[1])];custom_dsn.append({'uuid':row['uuid'],'placement_ast':place,'pin_ast':pin,'padstack_ast':stack})
# Cross-check retained controller correspondence exactly against independent raw AST lookup.
ck('236 connected2custom retained',s['dsn_correspondence']['terminal_count']==len(tokens)==236 and len(s['dsn_correspondence']['custom_pads'])==2)
for actual in custom_dsn:
    retained=next(x for x in s['dsn_correspondence']['custom_pads'] if x['uuid']==actual['uuid'])
    ck('retained custom DSN AST '+actual['uuid'],all(retained[k]==v for k,v in actual.items()))
ck('saved complete custom observation',s['custom_pad_observation']==c)
ck('native effective floor/net summary',s['native_effective_floors_nm']==o['floors_nm'] and s['native_effective_nets']==o['nets'])
for name,digest in s['stage_two_evidence'].items():ck('DRC stage frozen '+name,sha(OBS/name)==digest)
ck('DRC stage exact file census',set(s['stage_two_evidence'])=={'original-drc.json','original-drc-process.json','original-drc.log'})
binding=read(OBS/'original-drc-binding.json');target=OBS/'original-drc-input'/source.name
ck('nonsaving DRC complete original binding',binding['source']==str(OBS/'observe-input'/source.name) and binding['input']==str(target) and binding['saved'] is False and binding['before']==source_before)
after=inv(target.parent)
ck('DRC unchanged originals plus only disposable PRL',binding['after']==after and {k:after[k] for k in source_before}==source_before and set(after)-set(source_before)=={'pic_programmer.kicad_prl'})
ck('all final native binding SHA exact',s['native_binding']=={'board_sha256':sha(target),'project_sha256':sha(target.with_suffix('.kicad_pro')),'report_sha256':sha(OBS/'original-drc.json'),'binding_sha256':sha(OBS/'original-drc-binding.json')})
drcstep=read(OBS/'original-drc-process.json')
ck('DRC process declared exit5forwarnings',drcstep['status']=='nonzero_exit' and drcstep['exit_code']==5 and drcstep['cleanup_complete'] is True and drcstep['name']=='original-drc')
ck('DRC retained process equals step',all(s['steps'][1][key]==value for key,value in drcstep.items()))
ck('DRC exact nonsaving refill argv',drcstep['argv']==['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)','/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(OBS/'original-drc.json'),str(target)])
ck('DRC cwd/log and resource caps',drcstep['cwd']==str(OBS) and drcstep['log_bytes']==len(raw(OBS/'original-drc.log')) and drcstep['log_truncated'] is False and drcstep['resource_guards']==step['resource_guards'])
ck('DRC step actual input hash',s['steps'][1]['validated_input_sha256']==sha(source) and s['steps'][1]['emitted_candidate']==str(OBS/'observe-input'/source.name))
native=p.parse_report(OBS/'original-drc.json',source.name);report=read(OBS/'original-drc.json')
ck('actual report parse exactly summary',native==s['native'])
ck('native schema source/version',report['source']==source.name and report['kicad_version']=='10.0.0' and report['coordinate_units']=='mm' and report['$schema']=='https://schemas.kicad.org/drc.v1.json')
ck('native all severities report',set(report['included_severities'])=={'error','warning','exclusion'})
ck('native counters0/0/41/0',all(native[k]==v for k,v in {'opens':0,'blocking':0,'warnings':41,'exclusions':0}.items()) and len(native['findings'])==41)
ck('every actual finding missinglibrarywarning',all(x['severity']=='warning' and x['type']=='lib_footprint_issues' and x['description'].startswith('The current configuration does not include the footprint library ') for x in native['findings']))
ck('JP1 custom pads no native finding',not any(item['uuid'] in {x['uuid'] for x in before['pads']} for finding in native['findings'] for item in finding['items']))
project=read(source.with_suffix('.kicad_pro'));settings=project['board']['design_settings'];source_ignored=sorted(k for k,v in settings['rule_severities'].items() if v=='ignore');native_ignored=sorted(x['key'] for x in native['ignored_checks'])
ck('settings source bytes retained in observation',s['source_notes']['source_design_settings']==settings and s['source_notes']['source_net_settings']==project['net_settings'])
ck('ignored3source4native distinction',len(source_ignored)==3 and len(native_ignored)==4 and set(native_ignored)-set(source_ignored)=={'track_not_centered_on_via'} and 'track_not_centered_on_via' not in settings['rule_severities'])
ck('settings observations precise',s['settings_observation']['source_ignored_keys']==source_ignored and s['settings_observation']['native_ignored_keys']==native_ignored and s['settings_observation']['source_exclusions']==settings['drc_exclusions']==[] and s['settings_observation']['native_exclusions']==0 and s['settings_observation']['saved_fill_or_full_semantic_equivalence_observed'] is False)
ck('central counters pass but routing remainsfalse',s['central_native_policy_accepted'] is True and s['central_native_rejection_reasons']==p.native_rejection_reasons(native)==[] and s['routing_accepted'] is False)
try:p.preflight(source)
except p.Rejected as exc:gate=str(exc)
else:gate=None
ck('unchanged production preflight still rejects',gate==s['production_gate_rejection'])
ck('two stages accounting sums',abs(sum(x['cpu_seconds'] for x in s['steps'])-s['child_step_cpu_seconds'])<1e-9 and sum(x['wall_seconds'] for x in s['steps'])<=s['wall_seconds'] and s['total_cpu_seconds']>=s['child_step_cpu_seconds'])
ck('outer controller truly measuredexit0',execution['controller_exit_code']==0 and execution['argv']==['python3','-B','experiments/pic_custom_observer_v1/driver.py','--run-native','--output','.runs/pic-custom-observation-002'] and s['wall_seconds']<=execution['outer_wall_seconds']<60 and s['total_cpu_seconds']<=execution['waited_child_cpu_seconds']<60)
ck('entire completed evidence inventory exact',s['completed_evidence']=={k:v for k,v in inv(OBS).items() if k!='summary.json'})
ck('source unchanged and reportedtrue',s['original_inputs_unchanged'] is True and inv(source.parent)==source_before)
ck('run unchanged during audit',inv(OBS)==pre[str(OBS)])
result={'schema':1,'status':'audit_passed','checks':checks,'check_count':len(checks),'native_or_engine_executed_by_auditor':False,'routing_qualification_granted':False,'inputs':{'summary_sha256':sha(OBS/'summary.json'),'execution_sha256':sha(ROOT/'.runs/pic-custom-observation-002-execution.json')},'observations':{'status':s['status'],'native':native,'custom_pads':custom_rows,'dsn_connected_terminals':len(tokens),'native_DSN_ast':custom_dsn,'settings_observation':s['settings_observation'],'stored_prepublication_wall_seconds':s['wall_seconds'],'stored_prepublication_full_cpu_seconds':s['total_cpu_seconds'],'outer_execution':execution},'limits':['No routing was performed. Custom pad geometry/routing/format remain unqualified.','Original JP1 has no native DRC finding. This does not prove its exact mathematical clearance margin or qualify arbitrary custom polygons.','Native adds ignored track_not_centered_on_via absent from explicit source keys; no full settings semantic-equivalence claim.','Existing original376routes are source geometry, not a new engine outcome.'],'raw_inventory':pre[str(OBS)]}
(HERE/'audit-001.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'native':[native[k] for k in ('opens','blocking','warnings','exclusions')],'connected_terminals':len(tokens),'native_only_ignored':sorted(set(native_ignored)-set(source_ignored))},indent=2))
