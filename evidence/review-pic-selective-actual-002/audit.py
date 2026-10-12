"""Stored actual selective002 readback through existing comparator; no workers."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'experiments/custom_pad_area_probe_v1'))
from autorouter import placement_clearance as io
from experiments.custom_pad_area_probe_v1 import driver as base
inventory=lambda path:io.inventory(path,max_bytes=64*1024**2,max_files=2000,max_entries=4000)
read=lambda path:base.decode(base.content(path,16*1024**2))
run=ROOT/'.runs/pic-selective-area-observation-002';before=inventory(run);record=read(run/'summary.json');runtime=record['runtime']
source=ROOT/'.data/boards/kicad-pic-programmer';original=inventory(source)
assert original==runtime['original']==inventory(run/'observe-input')
assert all(before[k]==v for k,v in record['frozen_evidence'].items())
assert read(run/'runtime.json')==runtime
for rel,pin in runtime['sources'].items():assert base.content(run/'code'/rel,2*1024**2,digest=True)==pin
# Load the recorded namespace package first: ROOT is already developing later helpers.
sys.path.insert(0,str(run/'code'))
from experiments.pic_mixed_transport_probe_v1 import selective
for module in (selective,selective.transport,selective.ses_checks):
 assert Path(module.__file__).is_relative_to(run/'code')
protocol=read(run/'code/experiments/pic_mixed_transport_probe_v1/SELECTIVE_PROTOCOL.json')
assert protocol['mode']=='local250-selective' and protocol['cases']==[False]
assert protocol['basis']==runtime['basis']
assert runtime['tools']=={k:{x:v[x] for x in ('bytes','sha256')} for k,v in protocol['tools'].items()}
cached={}
for key,field in [('reuse_native','cached_native_inventory'),('reuse_local','cached_local_inventory')]:
 path=ROOT/protocol[key];cached[str(path)]=inventory(path);assert cached[str(path)]==runtime[field]
assert (run/'local-basis-observations.json').read_bytes()==(ROOT/protocol['reuse_local']/'observations.json').read_bytes()
observed=read(run/'observations.json');expected=read(run/'expectations.json');basis=read(run/'local-basis-observations.json')
comparison=selective.compare(observed,expected,basis);assert comparison==record['selective_comparison']
assert record['status']=='completed' and record['observations_complete'] is True
for flag in ('routing_accepted','custom_pad_support_qualified','mixed_clearance_equivalence_qualified','routing_executed','ses_executed','native_process_executed'):assert record[flag] is False
assert record['import_process_executed'] is True
row=observed['case'];entries=row['predicates_before']['tree_entries'];kinds=Counter(x['kind'] for x in entries)
assert row['predicates_before']['tree_entries']==row['predicates_after']['tree_entries']
for phase in ('predicates_before','predicates_after'):
 p=row[phase]
 assert p['all_tree_entries_valid'] is False and p['search_tree_population_verified'] is True
 assert (p['indexed_items'],p['unindexed_zero_shape_outlines'],len(p['tree_entries']))==(603,619,1222)
 assert sum(x['valid'] is False for x in p['tree_entries'])==619
 for x in p['tree_entries']:
  if x['kind']=='app.freerouting.board.model.items.ComponentOutline':assert (x['shape_count'],x['tile_shape_count'],x['entry_count'],x['on_board'],x['valid'])==(0,0,None,True,False)
  else:assert x['shape_count']>0 and x['entry_count']==x['shape_count'] and x['valid'] is True and x['on_board'] is True
old={x['id']:x for x in row['state']['areas']};new={x['id']:x for x in row['state_after_selective']['areas']}
assert set(old)==set(new)=={2,1221,1222} and old[2]==new[2]
assert old[2]['nets']==['GND'] and old[2]['obstacle'] is False
assert all(old[x]['obstacle'] is False and new[x]['obstacle'] is True for x in (1221,1222))
assert row['state']['ignore_conduction'] is True and row['state_after_selective']['ignore_conduction'] is False
assert row['route_geometry_before_local']==row['route_geometry']==row['route_geometry_after_selective']
assert row['settings_after']==row['settings_after_selective']
assert [x['name'] for x in record['steps']]==['compile','import']
tools=protocol['tools'];code=run/'code/experiments/pic_mixed_transport_probe_v1';jar=str(ROOT/tools['jar']['path']);home=str(run/'home')
argvs=[[*base.SANDBOX,tools['javac']['path'],'-J-Xmx256m','-J-Duser.home='+home,'-proc:none','-classpath',jar,'-d',str(run/'classes'),str(code/'MixedClassProbe.java'),str(run/'code/experiments/custom_pad_area_probe_v1/AreaContactProbe.java'),str(code/'SelectiveAreaProbe.java')],
 [*base.SANDBOX,tools['java']['path'],'-Xmx256m','-Djava.awt.headless=true','-Duser.home='+home,'-Djava.io.tmpdir='+str(run/'tmp'),'-cp',str(run/'classes')+':'+jar,'SelectiveAreaProbe',str(run/'mixed.dsn'),str(run/'observations.json')]]
processes=[]
for step,argv in zip(record['steps'],argvs):
 proc=read(run/(step['name']+'-process.json'));assert dict(proc,name=step['name'])==step
 assert proc['argv']==argv and proc['cwd']==str(run) and proc['exit_code']==0 and proc['status']=='success'
 assert proc['cleanup_complete'] is True and proc['log_truncated'] is False
 log=run/(step['name']+'.log');assert proc['log']==str(log) and proc['log_bytes']==log.stat().st_size
 processes.append({k:step[k] for k in ('name','wall_seconds','cpu_seconds','max_rss_bytes','exit_code')})
assert 0<record['wall_seconds']<180 and 0<record['total_cpu_seconds']<180
outer=read(ROOT/'.runs/pic-selective-area-observation-002-execution.json')
assert outer['git_head']==runtime['git']['head'] and outer['exit_code']==0
for name,key in [('run-pic-selective-area-observation-002.py','wrapper_sha256'),('pic-selective-area-observation-002-command.log','log_sha256')]:assert hashlib.sha256((ROOT/'.runs'/name).read_bytes()).hexdigest()==outer[key]
assert inventory(run)==before and inventory(source)==original
for path,pins in cached.items():assert inventory(Path(path))==pins
result={'passed':True,'scope':'Actual stored representation observation only; no fresh JVM/native/solver','head':runtime['git']['head'],'summary_sha256':before['summary.json'],'observations_sha256':before['observations.json'],'frozen_files':len(record['frozen_evidence']),'run_files':len(before),'captured_source_files':len(runtime['sources']),'original_files':len(original),'original_and_runs_unchanged':True,'comparison':comparison,'raw_tree_validation_false_preserved':619,'indexed_valid':603,'unindexed_zero_shape_null_outlines':619,'item_kinds':dict(kinds),'original_gnd_area_exact':True,'global_ignore_conduction_before':True,'global_ignore_conduction_after':False,'route_geometry_exact_before_after':True,'settings_exact_before_after':True,'parser_warnings':row['parser_warnings'],'trace_queries':{phase:{'count':len(row[phase]['trace_queries']),'clear':sum(x['tree_trace_check_clear'] for x in row[phase]['trace_queries']),'not_clear':sum(not x['tree_trace_check_clear'] for x in row[phase]['trace_queries'])} for phase in ('predicates_before','predicates_after')},'processes':processes,'stored_wall_seconds':record['wall_seconds'],'stored_full_cpu_seconds':record['total_cpu_seconds'],'outer_wall_seconds':outer['wall_seconds'],'outer_waited_cpu_seconds':outer['waited_child_cpu_seconds']}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
