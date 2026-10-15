"""Bounded read-only Native geometry screen; no route/DRC rerun or comparative acceptance."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,os,fcntl,stat
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,strategy as s,sexpr as sx,chain_proposals as cp,floor_route as f
O=R/'.runs/chain-native-route-screen-002';O.mkdir();tools=p.tool_manifest();rows=[]
inputs=[('Universal','evidence/universal-preparation950-actual-001/C-result.json'),('IR','.runs/ir-obstacle-corrected-cumulative300-003/feedback/C_feedback/result.json')]
fd=os.open(R/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW);lock=os.fdopen(fd,'r+');assert stat.S_ISREG(os.fstat(lock.fileno()).st_mode);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
record=dict(schema=1,passed=False,native_geometry_executed=True,routing_executed=False,drc_executed=False,comparison_eligible=False,new_gain=False,prior_native_requalified=False,tools=tools,script_sha256=p.sha(Path(__file__)),rows=rows,scope='Exposed retained generatedC candidates only. ActualNativepadgeometry on completecopy/pinnedhelper; no newrouting/DRC/quality/acceptance claim or sourceboardwrite. Everyzero/decline retained.')
try:
 for label,name in inputs:
  assert p.tool_manifest()==tools
  old=R/name;data=f.read_json(old);board=Path(data['candidate']);before=p.tree_hash(board.parent);tree=sx.read(board)
  row=dict(label=label,prior_result=name,prior_result_sha256=p.sha(old),candidate=str(board),candidate_sha256=p.sha(board),source_before=before);rows.append(row)
  job=p.Job(O/label,12,protect_local_settings=True)
  context,pin=s._chain_context(job,board);batch=cp.build(tree,s.zone_net_ids(tree),[r for r in p.routes(tree) if p.locked(r)],native_pads=context['pads'])
  assert p.sha(job.out/'floor-final-context.json')==pin and p.tree_hash(board.parent)==before and p.tool_manifest()==tools
  f.process_check(job.out,{'steps':job.steps},'floor-final',f.context_argv('final',job.out/'candidate'/board.name,job.out/'floor-final-context.json'))
  row.update(batch=batch,context_sha256=pin,steps=job.steps,input_unchanged=True,material=s._chain_context_inventory(job.out))
 assert max(time.monotonic()-START,cpu()-CPU0)+2<60;record['passed']=True
except BaseException as ex:record.update(passed=False,error=type(ex).__name__+': '+str(ex))
finally:
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
 p.save_json(O/'result.json',record);lock.close()
print(json.dumps({k:record.get(k) for k in ('passed','wall_seconds','full_cpu_seconds','error')}));print(json.dumps([{'label':r['label'],'groups':len(r.get('batch',{}).get('proposals',[])),'sizes':[v['segment_count'] for v in r.get('batch',{}).get('proposals',[])],'declined':r.get('batch',{}).get('declined_reason')} for r in rows]));raise SystemExit(0 if record['passed'] else 2)
