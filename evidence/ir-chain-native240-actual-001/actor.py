"""Fresh exposed IR five-arm mechanism comparison; existing paired driver plus own chains arm."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,copy,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,strategy as s
from scripts import experiment_paired as paired,experiment_quality as q
from experiments.native_paired_v1.observations import inventory,require
P=R/'.runs/ir-chain-fivearm-001-protocol.json';spec=f.read_json(P);O=Path(spec['output']);pin=p.sha(P)
def stable():
 q.verify_freeze(spec['freeze'],Path(spec['source']))
 require(p.sha(P)==pin and p.sha(Path(__file__))==spec['actor_sha256'],'prospective actor changed')
 for name,digest in spec['pins'].items():require(p.sha(R/name)==digest,'prospective supporting proof changed: '+name)
stable()
summary=paired.experiment(O/'run','ir-obstacle','native-all')
require(summary['status']=='completed','paired driver did not complete; preserve all attempted outcomes')
protocol=f.read_json(O/'run/protocol.json');require(protocol['freeze']==spec['freeze'],'paired freeze differs')
assigned=protocol['inner_allowance_seconds'];require(60<=assigned<=120,'inner allowance differs')
prior=inventory(O/'run');stable();start=time.monotonic();cp=cpu()
arm=dict(id='C_chains',adapter='both',engine_profile='tuned',operation='prune',proposal_policy='chains')
row=dict(arm,accepted=False,status='invocation_error',assigned_seconds=assigned)
cancelled=False
try:
 result=s.prune(Path(spec['source']),O/'C_chains',assigned,proposal_policy='chains')
 row.update(q.summarize(arm,O/'C_chains',result,time.monotonic()-start,cpu()-cp))
 cancelled=q.cancelled(result)
 require(result['budget_seconds']==result['cpu_budget_seconds']==assigned,'chains assignment differs')
 require(result['tools']==spec['tools'] and result['source_hashes']==spec['source_hashes'],'chains source differs')
 row.update(observations=q.observations(O/'C_chains',result,row),zone_net_ids=result.get('zone_net_ids'),pruning_trial_count=len(result.get('trials',[])),pruning_improvements=result.get('improvements'))
except (Exception,KeyboardInterrupt) as exc:
 cancelled=isinstance(exc,KeyboardInterrupt)
 row.update(accepted=False,status='cancelled' if cancelled else 'invocation_error',cancelled=cancelled,reason=type(exc).__name__+': '+str(exc))
finally:
 row.update(invocation_wall_seconds=time.monotonic()-start,invocation_cpu_seconds=cpu()-cp)
 row['accepted']=row['accepted'] and max(row['invocation_wall_seconds'],row['invocation_cpu_seconds'])<=120
 p.save_json(O/'chain-invocation.json',row)
stable();require(inventory(O/'run')==prior,'completed baseline/feedback arms changed')
record=dict(schema=1,status='cancelled' if cancelled else 'completed',arm_order=spec['arm_order'],rows=[*summary['results'],row],wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
p.save_json(O/'actor-result.json',record);print(json.dumps({'status':record['status'],'rows':[{k:r.get(k) for k in ('id','status','accepted','length_mm','vias','pruning_trial_count','pruning_improvements','reason')} for r in record['rows']]}))

raise SystemExit(130 if cancelled else 0)
