"""Read-only recovery of completed native stages, retaining invalid receipt.
No Native process, source or completed artifact is modified.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('saved_driver',ROOT/'.runs/inner-pour-saved-native-001.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
from autorouter import pipeline as p,floor_route as f,config as c,local_settings as ls,handoff as h,sexpr as sx
plan=f.read_json(d.BASE/'protocol.json');pin=p.sha(d.BASE/'protocol.json');d.context(plan,pin)
execution=d.BASE/'execution';worker=execution/'worker';raw=f.read_json(worker/'result.json');enclosure=f.read_json(execution/'execution.json')
if raw['status']!='invalidated' or raw['reason']!='Rejected: normal DRC producer source pin differs':raise p.Rejected('retained harness failure differs')
if enclosure['child_sha256']!=p.sha(worker/'result.json')or enclosure['process']['cleanup_complete']is not True or enclosure['process']['exit_code']!=0:raise p.Rejected('original process binding changed')
if d.existing.material(worker)!=raw['completed_evidence']:raise p.Rejected('completed saved native tree changed')
out=ROOT/'.runs/inner-pour-saved-readback-001';out.mkdir();owner={};h.capture_destination(owner,out)
rows=[]
for row in raw['cases']:
 name=row['case'];job=worker/name;board=job/'saved'/(plan['metadata_protocol']['stem']+'.kicad_pcb')
 observed=f.check_drc_stage(job,{'steps':row['steps']},'saved-refill',board,board,True,row['before'],schematic_parity=True)
 if observed!=row['native']:raise p.Rejected('shared saved stage differs')
 tools=plan['metadata_protocol']['tools']
 if any(p.sha(job/'code'/Path(n).name)!=value for n,value in tools['implementation_sha256'].items()):raise p.Rejected('captured product differs')
 # This harness used a protected_step metadata sidecar with reserved binding
 # suffix/fields. It is not a Job.drc binding; retain the census refusal too.
 try:ls.check_normal_policy(job,{'steps':row['steps'],'tools':tools},max_bytes=d.existing.LIMIT,max_files=2048)
 except p.Rejected as exc:policy_refusal=str(exc)
 else:raise p.Rejected('expected metadata-journal incompatibility absent')
 if policy_refusal!='normal DRC worker census differs from retained evidence':raise p.Rejected('unexpected policy refusal: '+policy_refusal)
 ls.check_event(job,row['metadata_binding'],row['metadata_process'])
 output=job/'metadata-after-save.json';metadata=f.read_json(output);argv=[c.PYTHON,'-B',d.m.__file__,'--native',output,board]
 f.process_check(job,{'steps':row['steps']},'metadata-after-save',[*f.SANDBOX,*map(str,argv)])
 if p.sha(output)!=row['metadata_sha256']or metadata!=row['metadata']or metadata['input_hashes_before']!=row['after']or metadata['input_hashes_after']!=row['after']or metadata['loaded_pcbnew_sha256']!=p.sha(c.PCBNEW):raise p.Rejected('metadata proof differs')
 source=d.m.BASE/'sources'/name/board.name;original=sx.read(source);saved=sx.read(board)
 try:
  transplanted=p.transplant_fill(original,saved);transplant=dict(succeeded=True,original_nonfill_preserved=p.immutable(original)==p.immutable(transplanted),original_routes_preserved=p.routes(original)==p.routes(transplanted))
 except p.Rejected as exc:transplant=dict(succeeded=False,error='Rejected: '+str(exc))
 if transplant!=row['transplant']:raise p.Rejected('transplant diagnosis differs')
 rows.append(dict(case=name,shared_saved_stage_replayed=True,native={k:observed[k]for k in('opens','blocking','warnings','exclusions','ignored_checks')},saved_board_sha256=p.sha(board),saved_area_metadata=row['saved_area_metadata'],transplant=transplant,metadata=metadata['observation'],normal_policy_census_refusal=policy_refusal))
result=dict(schema=1,status='diagnostic_readback_complete',accepted=False,qualified=False,production_support_qualified=False,source_head=plan['metadata_protocol']['source_head'],original_receipt_status=raw['status'],original_receipt_reason=raw['reason'],outer_observation_complete_flag_ignored=True,original_receipt_sha256=p.sha(worker/'result.json'),original_enclosure_sha256=p.sha(execution/'execution.json'),original_process_costs={k:enclosure[k]for k in('wall_seconds','full_CPU_seconds')},cases=rows,all_saved_board_bytes_identical=len({row['saved_board_sha256']for row in rows})==1,scope='Read-only shared per-stage native replay and metadata event checks only. Complete normal-policy journal census refuses the harness non-DRC metadata binding. No new native run or production qualification.')
witness=d.existing.material(execution)
def stable():
 h.owned_destination(owner);d.context(plan,pin)
 if d.existing.material(execution)!=witness:raise p.Rejected('original evidence changed')
def account():result.update(wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0)
f.publish(out,result,stable,account,lambda:10-(time.monotonic()-START),owned=lambda:h.owned_destination(owner),final_check=stable)
print(json.dumps({k:result[k]for k in('status','all_saved_board_bytes_identical','wall_seconds','full_CPU_seconds')}))
raise SystemExit(0 if result['status']=='diagnostic_readback_complete'else 2)
