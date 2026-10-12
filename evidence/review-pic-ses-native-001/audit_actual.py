"""Compact original-rule/stop-boundary audit using existing helpers; no native rerun."""
from pathlib import Path
import hashlib,json,sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d,ses_checks as c,ses_native as n
from autorouter import pipeline as p,sexpr as sx
RUN=ROOT/'.runs/pic-custom-ses-native-001';before=d.inventory(RUN);record=d.base.decode(d.base.content(RUN/'summary.json'))
original_path=d.original.SOURCE;original_before=d.inventory(original_path.parent)
assert record['status']=='failed' and record['error']=='Rejected: candidate project/rules/file set changed'
assert record['observations_complete'] is False and record['routing_accepted'] is False
assert record['runtime']['original']==original_before==d.inventory(RUN/'observe-input')
assert all(before[k]==v for k,v in record['frozen_evidence'].items())
assert d.base.decode(d.base.content(RUN/'runtime.json'))==record['runtime']
for rel,pin in record['runtime']['sources'].items():assert d.base.content(RUN/'code'/rel,digest=True)==pin
assert [r['name'] for r in record['steps']]==['ses-baseline','ses-import-positive']
processes=[]
for row in record['steps']:
 actual=d.base.decode(d.base.content(RUN/(row['name']+'-process.json')))
 assert actual=={k:v for k,v in row.items() if k!='name'}
 assert actual['exit_code']==(5 if row['name']=='ses-baseline' else 0) and actual['cleanup_complete'] is True
 assert actual['log_truncated'] is False and actual['cwd']==str(RUN/'ses-native')
 processes.append({k:row[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','max_rss_bytes')})
baseline=p.parse_report(RUN/'ses-native/baseline.json',original_path.name)
assert baseline==record['native_ses']['baseline']
assert (baseline['opens'],baseline['blocking'],baseline['warnings'],baseline['exclusions'])==(0,0,41,0)
binding=d.base.decode(d.base.content(RUN/'ses-native/baseline-binding.json'))
assert binding['saved'] is False and binding['before']==original_before
assert d.inventory(Path(binding['input']).parent)==binding['after']
p.check_drc_project(binding['before'],binding['after'],original_path.name,saved=False)
raw=RUN/'ses-native/raw-positive'/original_path.name
old=sx.read(original_path);new=sx.read(raw)
assert p.immutable(old)==p.immutable(new)
a,b=c.source_routes(old);x,y=c.source_routes(new)
assert b==y
old_project=d.base.decode(d.base.content(original_path.with_suffix('.kicad_pro')));new_project=d.base.decode(d.base.content(raw.with_suffix('.kicad_pro')))
deltas=[]
def compare(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(a.keys()|b.keys()):
   if k not in a:deltas.append({'path':path+'/'+k,'change':'added','after':b[k]})
   elif k not in b:deltas.append({'path':path+'/'+k,'change':'removed','before':a[k]})
   else:compare(a[k],b[k],path+'/'+k)
 elif a!=b:deltas.append({'path':path,'change':'changed','before':a,'after':b})
compare(old_project,new_project)
assert deltas==[{'path':'/board/design_settings/rule_severities/track_not_centered_on_via','change':'added','after':'ignore'},{'path':'/board/ipc2581/bom_rev','change':'added','after':''},{'path':'/board/ipc2581/sch_revision','change':'added','after':''}],deltas
rawfiles=d.inventory(raw.parent)
assert set(rawfiles)-set(original_before)=={original_path.with_suffix('.kicad_prl').name}
assert all(rawfiles[k]==v for k,v in original_before.items() if k not in (original_path.name,original_path.with_suffix('.kicad_pro').name))
try:p.verify_candidate_files(raw,original_before)
except p.Rejected as exc:guard=str(exc)
else:raise AssertionError('changed project guard failed')
for name in ('raw-positive-drc.json','negative-drc.json','final-drc.json','raw-negative','candidate'):
 assert not (RUN/'ses-native'/name).exists(),name
assert record['native_ses']['candidate_emitted'] is False
outer=d.base.decode(d.base.content(ROOT/'.runs/pic-custom-ses-native-001-execution.json'))
assert outer['git_head']==record['runtime']['git']['head'] and outer['exit_code']==1
assert outer['wrapper_sha256']==hashlib.sha256((ROOT/'.runs/run-pic-custom-ses-native-001.py').read_bytes()).hexdigest()
assert outer['log_sha256']==hashlib.sha256((ROOT/'.runs/pic-custom-ses-native-001-command.log').read_bytes()).hexdigest()
assert d.inventory(RUN)==before and d.inventory(original_path.parent)==original_before
result={'passed':True,'scope':'Stored failed native001 diagnosis; no new processes','head':record['runtime']['git']['head'],'summary_sha256':before['summary.json'],'frozen_files':len(record['frozen_evidence']),'complete_run_files':len(before),'source_pins':len(record['runtime']['sources']),'original_files':len(original_before),'original_and_run_unchanged':True,'processes':processes,'baseline':{k:baseline[k] for k in ('opens','blocking','warnings','exclusions','ignored_checks')},'warning_types':dict(Counter(v['type'] for v in baseline['findings'])),'raw_board_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'raw_immutable_equal':True,'original_segments':sum(a.values()),'raw_segments':sum(x.values()),'routes':c.diff(a,x),'vias_equal':True,'project_deltas':deltas,'added_file':original_path.with_suffix('.kicad_prl').name,'guard_rejection':guard,'unreached':['positive DRC','negative import','negative DRC','candidate emission'],'stored_wall_seconds':record['wall_seconds'],'stored_cpu_seconds':record['total_cpu_seconds'],'outer_wall_seconds':outer['wall_seconds'],'outer_waited_cpu_seconds':outer['waited_child_cpu_seconds']}
(OUT/'actual.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('routes','baseline')}))
