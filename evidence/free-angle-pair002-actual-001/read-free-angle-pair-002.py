"""Replay the frozen experiment through the shared readers; no Native/JAR run."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from experiments.native_paired_v1 import observations as obs
module=ROOT/'.runs/run-free-angle-pair-002.py';spec=importlib.util.spec_from_file_location('frozen_angle_pair',module);c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
PIN='ad7d017022afcfbdcecf0f4721ed95823507145bf1c9d46909e0a65aabb19b90'
plan=f.read_json(c.PROTOCOL);c.context(plan,PIN);witness={};rows=[]
def remember(q):witness[str(q)]=p.sha(q)
def timing(q):
 remember(q);values={k:float(v) for k,v in re.findall(r'^(real|user|sys) ([0-9.]+)$',q.read_text(),re.M)}
 if set(values)!={'real','user','sys'}:raise p.Rejected('actual complete-command time unavailable')
 return values
for project,angle in c.ORDER:
 outer_path=c.OUT/project/angle/'result.json';outer=f.read_json(outer_path);remember(outer_path)
 recovered=(project,angle)==c.ORDER[0]
 child_path=c.OLD_CHILD/'result.json' if recovered else outer_path.parent/'child/result.json'
 child=f.read_json(child_path);remember(child_path);route=child_path.parent/'route';receipt=route/'result.json';data=f.read_json(receipt);remember(receipt)
 cfg=plan['projects'][project];board=Path(cfg['source']);source=p.sx.read(board)
 if c.shared.material(child_path.parent)!=child['completed_evidence']:raise p.Rejected('completed child material differs')
 c.same_tools(data['tools'],cfg['freeze']['tools'])
 if data['source_hashes']!=cfg['freeze']['source_hashes']:raise p.Rejected('original source differs')
 with p.validation_readback_session():
  workers=obs.workers(route,data,board,cfg['freeze']['source_hashes'],source)
  error=obs.resource_failure(route,data)
  candidate=obs.candidate(route,data,board,source,cfg['freeze']['source_hashes'],cfg['baseline'],resource_error=error) if (route/'final-drc.json').is_file() else None
  expected=dict(id=angle,adapter='both',engine_profile=c.PROFILES[angle],operation='route')
  row=c.q.summarize(expected,route,data,child['row']['invocation_wall_seconds'],child['row']['invocation_cpu_seconds']);row['observations']=c.q.observations(route,data,row)
  if row['accepted']:p.check_result(receipt)
 if f.canonical(row)!=f.canonical(child['row']) or f.canonical(workers)!=f.canonical(child['workers']) or error!=child['resource_failure'] or f.canonical(candidate)!=f.canonical(child.get('candidate')):raise p.Rejected('fresh shared replay differs from retained complete observation')
 if bool(outer['passed'])!=bool(row['accepted']):raise p.Rejected('outer route qualification differs')
 label='ir' if project=='ir-obstacle' else 'arcdice'
 name='ir-stock45-recovery-time.log' if recovered else label+'-'+angle+'-time.log'
 t=timing(ROOT/'.runs/free-angle-pair-execution-002'/name)
 prior_wall=33.35 if recovered else 0.;prior_cpu=31.88 if recovered else 0.
 wall=t['real']+prior_wall+plan['preparation_costs']['wall_seconds']+2
 cpu=t['user']+t['sys']+prior_cpu+plan['preparation_costs']['full_cpu_seconds']+2
 if max(wall,cpu)+.02>240:raise p.Rejected('actual complete command and preparation exceed delivered budget')
 rows.append(dict(project=project,angle=angle,passed=row['accepted'],row=row,original_outer_status=outer['status'],retained_first=recovered,
  full_command=t,complete_command_and_preparation_wall_seconds=wall,complete_command_and_preparation_full_cpu_seconds=cpu,
  time_rounding_upper_allowance_seconds=.02,shared_worker_count=len(workers),resource_failure=error,candidate=candidate))
c.context(plan,PIN)
if any(p.sha(Path(q))!=pin for q,pin in witness.items()):raise p.Rejected('retained experiment inputs changed during replay')
for project,angle in c.ORDER:
 folder=c.OLD_CHILD/'route' if (project,angle)==c.ORDER[0] else c.OUT/project/angle/'child/route'
 c.ls.check_normal_policy(folder,f.read_json(folder/'result.json'),max_bytes=c.LIMITS['output'],max_files=2048)
record=dict(schema=1,shared_replay_passed=True,all_routes_accepted=all(x['passed'] for x in rows),protocol_sha256=PIN,controller_sha256=p.sha(module),reader_sha256=p.sha(Path(__file__)),rows=rows,exact_read_inputs_sha256=witness,new_native_or_jar_execution=False,
 scope='Whole four-arm population retained, including timeout. Actual complete command timing substitutes sampled outer totals; reader full-command costs must be added from enclosing time log before final240 cap claim. No generalization/C/novelty/speedup/whole-project-clean/default/release claim.')
p.save_json(Path(sys.argv[1])/'reader.json',record);print(f.canonical(dict(shared_replay_passed=True,arms=len(rows),accepted=sum(x['passed'] for x in rows))))
