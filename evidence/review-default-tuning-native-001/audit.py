"""Compact shared receipt/native-report readback; no native execution."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;D=R/'.runs/default-tuning-native-001'
sys.dont_write_bytecode=True;sys.path.insert(0,str(R))
from autorouter import pipeline as p,placement_clearance as io,netclass as n,sexpr as sx
read=lambda q:io.read_bytes(q,16*1024**2);sha=lambda q:hashlib.sha256(read(q)).hexdigest();load=lambda q:json.loads(read(q))
s=load(D/'result.json');source=Path(s['source']);candidate=Path(s['candidate']);before=io.evidence_inventory(D);sourcebefore=io.inventory(source.parent)
assert sourcebefore==s['source_hashes']==io.inventory(D/'snapshot')
result=p.check_result(D/'result.json');assert result['current'] is True and result['candidate_sha256']==s['candidate_sha256']==sha(candidate)
assert s['tools']['git_head']=='99456722fc78019d155057bbb361690b4f8f9c92'
assert s['tools']['implementation_sha256']['autorouter/netclass.py']=='96a7425112bc5a5ce5d2f15f69efc334fbfbb97aa9deee1ee33ce984d25a8ea6'
assert s['tools']['implementation_sha256']['autorouter/pipeline.py']=='266ffd1fb0ec4fea30a4b7d73df9d387c727b690ef2b13f3eeda6870cbd6a8fa'
parsed=p.parse_report(D/'final-drc.json',candidate.name);assert parsed==s['native']
assert all(parsed[k]==0 for k in ['opens','blocking','warnings','exclusions']) and parsed['findings']==[]
assert sha(D/'final-drc.json')==s['native_report_sha256']
assert p.immutable(sx.read(source))==p.immutable(sx.read(candidate)) and s['invariants_unchanged'] is True
assert source.with_suffix('.kicad_pro').read_bytes()==candidate.with_suffix('.kicad_pro').read_bytes()
n.reject_tuning_intent(load(source.with_suffix('.kicad_pro')))
p.verify_candidate_files(candidate,s['source_hashes'],s['candidate_sha256'])
binding=load(D/'final-drc-binding.json');assert binding['before'][source.name]==s['candidate_sha256'] and binding['saved'] is False
p.check_drc_project(binding['before'],binding['after'],source.name)
assert binding['after']==io.inventory(D/'final-drc-input')
steps=[]
for stage in s['steps']:
 process=load(D/(stage['name']+'-process.json'))
 assert all(stage[k]==v for k,v in process.items())
 extras=set(stage)-set(process)
 assert extras<= {'name','validated_input_sha256','emitted_candidate'}
 if 'validated_input_sha256' in extras:
  b=load(D/(stage['name']+'-binding.json'));name=Path(b['input']).name
  assert stage['validated_input_sha256']==b['before'][name] and stage['emitted_candidate']==b['source']
  p.check_drc_project(b['before'],b['after'],name,saved=b['saved'])
  assert b['after']==io.inventory(Path(b['input']).parent)
 assert stage['status']=='success' and stage['exit_code']==0 and stage['cleanup_complete'] is True
 assert not stage['log_truncated'] and Path(stage['log'])==D/(stage['name']+'.log')
 assert Path(stage['cwd'])==D
 steps.append({k:stage[k] for k in ['name','status','exit_code','wall_seconds','cpu_seconds','monitor_cpu_seconds','max_rss_bytes','cleanup_complete']})
assert [v['name'] for v in steps]==['source-drc','floor-export','engine','import','refill-drc','floor-final','final-drc','metrics']
metrics=load(D/'metrics.json');assert metrics==s['metrics'] and metrics['vias']==1 and metrics['track_length_mm']==67.93373808491306
assert s['budget_seconds']==s['cpu_budget_seconds']==60 and 0<s['wall_seconds']<60 and 0<s['total_cpu_seconds']<60
assert abs(s['total_cpu_seconds']-sum(s[k] for k in ['parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds']))<1e-8
outer=load(R/'.runs/default-tuning-native-001-execution.json');assert outer['exit_code']==0 and outer['git_head']==s['tools']['git_head']
assert outer['log_sha256']==sha(R/'.runs/default-tuning-native-001-command.log')
assert before==io.evidence_inventory(D) and sourcebefore==io.inventory(source.parent)
out={'schema':1,'passed':True,'scope':'Fresh owned-fixture native compatibility evidence readback, not new routing or comparison. No native/JVM work performed by review.',
 'checker_result':result,'run_head':s['tools']['git_head'],'source_file_count':len(sourcebefore),'run_file_count':len(before),
 'bound_artifacts':{q.name:sha(q) for q in [D/'result.json',D/'final-drc.json',D/'final-drc-binding.json',D/'metrics.json',source,source.with_suffix('.kicad_pro')]},
 'candidate_sha256':sha(candidate),'native':parsed,'metrics':metrics,'steps':steps,'wall_seconds':s['wall_seconds'],'total_cpu_seconds':s['total_cpu_seconds'],
 'outer':outer,'whole_project_drc_clean':s['whole_project_drc_clean'],'source_and_candidate_project_identical':True,'source_and_run_unchanged':True,'native_jobs':0,'jvm_jobs':0}
(H/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'stages':len(steps),'native':{k:parsed[k] for k in ['opens','blocking','warnings','exclusions']}}))
