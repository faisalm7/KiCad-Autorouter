"""Bounded read-only Native geometry screen; no route/DRC rerun or comparative acceptance."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,os,fcntl,stat
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,strategy as s,sexpr as sx,chain_proposals as cp,floor_route as f
O=R/'.runs/chain-geometry-cohort003';O.mkdir();tools=p.tool_manifest();rows=[]
protocol=R/'.runs/chain-geometry-cohort003-protocol.json';spec=f.read_json(protocol);protocol_pin=p.sha(protocol);assert spec['tools']==tools
inputs=spec['inputs']
fd=os.open(R/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW);lock=os.fdopen(fd,'r+');assert stat.S_ISREG(os.fstat(lock.fileno()).st_mode);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
record=dict(schema=1,passed=False,native_geometry_executed=True,routing_executed=False,drc_executed=False,comparison_eligible=False,new_gain=False,prior_native_requalified=False,tools=tools,script_sha256=p.sha(Path(__file__)),rows=rows,scope='Exposed retained generatedC candidates only. ActualNativepadgeometry on completecopy/pinnedhelper; no newrouting/DRC/quality/acceptance claim or sourceboardwrite. Everyzero/decline retained.')
try:
 for item in inputs:
  label,name=item['label'],item['result']
  assert p.tool_manifest()==tools
  old=R/name;data=f.read_json(old);board=Path(data['candidate']);before=p.tree_hash(board.parent);tree=sx.read(board)
  assert p.sha(old)==item['result_sha256'] and p.sha(board)==item['candidate_sha256'] and before==item['project_sha256'] and p.sha(protocol)==protocol_pin
  row=dict(label=label,prior_result=name,prior_result_sha256=p.sha(old),candidate=str(board),candidate_sha256=p.sha(board),source_before=before);rows.append(row)
  copper=[v for v in sx.one(tree,'layers')[1:] if isinstance(v,list) and len(v)>1 and sx.unquote(v[1]).endswith('.Cu')]
  if len(copper)!=2:
   row.update(geometry_executed=False,unsupported='existing Native geometry helper requires2Cu; actual'+str(len(copper)));continue
  job=p.Job(O/label,12,protect_local_settings=True)
  context,pin=s._chain_context(job,board);batch=cp.build(tree,s.zone_net_ids(tree),[r for r in p.routes(tree) if p.locked(r)],native_pads=context['pads'])
  assert p.sha(job.out/'floor-final-context.json')==pin and p.tree_hash(board.parent)==before and p.tool_manifest()==tools
  f.process_check(job.out,{'steps':job.steps},'floor-final',f.context_argv('final',job.out/'candidate'/board.name,job.out/'floor-final-context.json'))
  row.update(batch=batch,context_sha256=pin,steps=job.steps,input_unchanged=True,material=s._chain_context_inventory(job.out))
 prior=f.read_json(R/spec['reused_two']);assert p.sha(R/spec['reused_two'])==spec['reused_two_sha256'] and prior['passed'] is True and prior['tools']==tools
 for row in prior['rows']:
  assert s._chain_context_inventory(Path(row['steps'][0]['cwd']))==row['material'] and p.tree_hash(Path(row['candidate']).parent)==row['source_before']
 record['reused_rows']=prior['rows'];record['reused_receipt_sha256']=spec['reused_two_sha256'];record['protocol_sha256']=protocol_pin
 assert max(time.monotonic()-START,cpu()-CPU0)+2<60;record['passed']=True
except BaseException as ex:record.update(passed=False,error=type(ex).__name__+': '+str(ex))
finally:
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
 p.save_json(O/'result.json',record);lock.close()
print(json.dumps({k:record.get(k) for k in ('passed','wall_seconds','full_cpu_seconds','error')}));print(json.dumps([{'label':r['label'],'groups':len(r.get('batch',{}).get('proposals',[])),'sizes':[v['segment_count'] for v in r.get('batch',{}).get('proposals',[])],'declined':r.get('batch',{}).get('declined_reason')} for r in rows]));raise SystemExit(0 if record['passed'] else 2)
