"""Compact shared-helper readback of actual native002; no execution of native workers."""
from pathlib import Path
import hashlib,json,sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d,ses_native as n,ses_checks as c
from autorouter import pipeline as p,sexpr as sx
run=ROOT/'.runs/pic-custom-ses-native-002';before=d.inventory(run);read=n.floor.read_json
record=read(run/'summary.json');runtime=record['runtime'];res=record['native_ses'];source=d.original.SOURCE
original_before=d.inventory(source.parent)
assert runtime['original']==original_before==d.inventory(run/'observe-input')
assert all(before[k]==v for k,v in record['frozen_evidence'].items())
assert read(run/'runtime.json')==runtime
for rel,pin in runtime['sources'].items():
 assert d.base.content(run/'code'/rel,2*1024**2,digest=True)==pin
 assert d.base.content(ROOT/rel,2*1024**2,digest=True)==pin
protocol=read(run/'code/experiments/pic_mixed_transport_probe_v1/SES_FINISH_PROTOCOL.json')
assert protocol['basis']==runtime['basis']
assert runtime['tools']=={k:{x:v[x] for x in ('bytes','sha256')} for k,v in protocol['tools'].items()}
cached_runs={}
for key,field in [('reuse_native','cached_native_inventory'),('reuse_ses','cached_ses_inventory'),('reuse_positive','cached_positive_inventory')]:
 path=ROOT/protocol[key];cached_runs[str(path)]=d.inventory(path)
 assert cached_runs[str(path)]==runtime[field]
base,oldraw,binding=n.cached_positive(ROOT/protocol['reuse_positive'],runtime,runtime['cached_positive_inventory'])
assert binding==res['native_reuse'] and base==res['baseline']
assert record['status']=='observed-incomplete' and record['observations_complete'] is False
for flag in ('routing_accepted','routing_executed','custom_pad_support_qualified','mixed_clearance_equivalence_qualified','import_process_executed'):assert record[flag] is False
assert record['ses_executed'] is True and record['ses_reuse']['new_writer_execution'] is False
work=run/'ses-native';positive=work/'positive-project'/source.name;negative=work/'negative-project'/source.name
raw=work/'raw-positive.kicad_pcb';bad=work/'raw-negative.kicad_pcb'
assert raw.read_bytes()==oldraw.read_bytes()==positive.read_bytes()
assert bad.read_bytes()==negative.read_bytes()
for board in (positive,negative):p.verify_candidate_files(board,original_before)
original=sx.read(source)
assert n.semantic_diff(original,sx.read(raw))==res['raw_immutable']=={'equal':True,'different_top_level_keys':[]}
assert n.semantic_diff(original,sx.read(bad))==res['negative_immutable']=={'equal':True,'different_top_level_keys':[]}
reports={};processes=[]
for name,board,key in [('raw-positive-drc',positive,'raw_native'),('negative-drc',negative,'negative_native')]:
 parsed=p.parse_report(work/(name+'.json'),source.name);assert parsed==res[key];reports[name]=parsed
 binding2=read(work/(name+'-binding.json'));inputboard=work/(name+'-input')/source.name
 assert binding2['saved'] is False and binding2['source']==str(board) and binding2['input']==str(inputboard)
 assert binding2['before']==d.inventory(board.parent) and binding2['after']==d.inventory(inputboard.parent)
 p.check_drc_project(binding2['before'],binding2['after'],source.name,saved=False)
 assert all(binding2['before'][k]==v for k,v in original_before.items() if k!=source.name)
assert n.same_findings(base,reports['raw-positive-drc']) and res['raw_findings_equal'] is True
assert [(reports[k][x] for x in ()) for k in ()]==[]
assert tuple(reports['raw-positive-drc'][k] for k in ('opens','blocking','warnings','exclusions'))==(0,0,41,0)
assert tuple(reports['negative-drc'][k] for k in ('opens','blocking','warnings','exclusions'))==(10,0,41,0)
rawtree=sx.parse((run/'raw.ses').read_text());expected=read(run/'expectations.json')
invalid,recipe=c.disconnected(rawtree,original,expected)
assert invalid==(run/'disconnected.ses').read_bytes() and recipe==res['negative_recipe']
ids={sx.unquote(sx.one(pad,'uuid')[1]) for fp in sx.children(original,'footprint') for pad in sx.children(fp,'pad') if sx.one(pad,'net')==['net','"'+recipe['net']+'"']}
findings=n.negative_findings(base,reports['negative-drc'],read(work/'negative-drc.json'),ids,recipe['net'])
assert findings==res['negative_required_findings'] and len(findings)==10
jp1=next(fp for fp in sx.children(original,'footprint') if any(sx.unquote(q[1])=='Reference' and sx.unquote(q[2])=='JP1' for q in sx.children(fp,'property')))
jpid=next(sx.unquote(sx.one(pad,'uuid')[1]) for pad in sx.children(jp1,'pad') if sx.unquote(pad[1])=='2')
assert any(i.get('uuid')==jpid for f in findings for i in f['items'])
a,b=c.source_routes(sx.read(raw));x,y=c.source_routes(sx.read(bad))
assert Counter({k:v for k,v in a.items() if k[0]!=recipe['net']})==x
assert Counter({k:v for k,v in b.items() if k[0]!=recipe['net']})==y
assert record['ses_transport']['exact_route_survival'] is False and res['raw_routes']['equal'] is False
assert not res['candidate_emitted'] and not res['completed'] and not (work/'candidate').exists()
assert [s['name'] for s in record['steps']]==['ses-raw-positive-drc','ses-import-negative','ses-negative-drc']
for row in record['steps']:
 proc=read(run/(row['name']+'-process.json'));assert dict(proc,name=row['name'])==row
 code=0 if row['name']=='ses-import-negative' else 5
 if code==0:argv=[*n.floor.SANDBOX,str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'import',str(run/'observe-input'/source.name),str(bad),str(run/'disconnected.ses')]
 else:
  name=row['name'][4:];argv=[*n.floor.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(work/(name+'.json')),str(work/(name+'-input')/source.name)]
 assert proc['argv']==argv and proc['cwd']==str(work) and proc['exit_code']==code
 assert proc['status']==('success' if code==0 else 'nonzero_exit') and proc['cleanup_complete'] and not proc['log_truncated']
 log=run/(row['name']+'.log');assert proc['log']==str(log) and proc['log_bytes']==log.stat().st_size
 processes.append({k:row[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','max_rss_bytes')})
assert 0<record['wall_seconds']<180 and 0<record['total_cpu_seconds']<180
outer=read(ROOT/'.runs/pic-custom-ses-native-002-execution.json')
assert outer['git_head']==runtime['git']['head'] and outer['exit_code']==1
for path,key in [('.runs/run-pic-custom-ses-native-002.py','wrapper_sha256'),('.runs/pic-custom-ses-native-002-command.log','log_sha256')]:assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==outer[key]
assert d.inventory(run)==before and d.inventory(source.parent)==original_before
for path,pins in cached_runs.items():assert d.inventory(Path(path))==pins
report={'passed':True,'scope':'Stored actual native002 readback, no native/JVM rerun','head':runtime['git']['head'],'summary_sha256':before['summary.json'],'frozen_files':len(record['frozen_evidence']),'run_files':len(before),'source_pins':len(runtime['sources']),'original_files':len(original_before),'original_and_all_cached_runs_unchanged':True,'status':record['status'],'routing_accepted':False,'candidate_emitted':False,'exact_route_survival':False,'processes':processes,'reports':{k:{x:v[x] for x in ('opens','blocking','warnings','exclusions','ignored_checks')} for k,v in reports.items()},'warning_types':{k:dict(Counter(x['type'] for x in v['findings'] if x['severity']=='warning')) for k,v in reports.items()},'full_positive_findings_equal_baseline':True,'raw_positive_sha256':p.sha(raw),'raw_negative_sha256':p.sha(bad),'raw_immutable_equal':True,'negative_immutable_equal':True,'negative_recipe':recipe,'negative_errors':len(findings),'jp1_2_uuid':jpid,'jp1_2_target_present':True,'other_net_routes_exact':True,'prior_native_run_wall_seconds':res['native_reuse']['prior_run_wall_seconds'],'prior_native_run_cpu_seconds':res['native_reuse']['prior_run_total_cpu_seconds'],'stored_wall_seconds':record['wall_seconds'],'stored_cpu_seconds':record['total_cpu_seconds'],'outer_wall_seconds':outer['wall_seconds'],'outer_waited_cpu_seconds':outer['waited_child_cpu_seconds']}
(OUT/'actual002.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
