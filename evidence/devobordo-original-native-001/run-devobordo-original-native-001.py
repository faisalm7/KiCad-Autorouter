from pathlib import Path
import sys,time,json,shutil,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,sexpr as sx,floor_route as f,placement_clearance as io
from autorouter.runner import run
from experiments.licensed_acquisition_v3 import native_snapshot
from experiments.placement_handoff_native_v1.driver import copy_bytes
OUT=ROOT/'.runs/devobordo-original-native-001';LIMIT=20*1024**2;SECONDS=90
start=time.monotonic();cpu0=time.process_time()+f.child_cpu()
def remaining():return min(SECONDS-(time.monotonic()-start),SECONDS-(time.process_time()+f.child_cpu()-cpu0))
def size():return sum(len(x) for x in io.inventory(OUT,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096).values())
class BoundJob(f.FloorJob):
 def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
  if remaining()<=0:raise p.Rejected('whole diagnostic budget exhausted')
  actual=[str(a) for a in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
  result=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=min(30,remaining()),env=self.env,max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
  result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
  if result['status'] not in ('success','nonzero_exit') or result['exit_code'] not in allowed or result.get('cleanup_complete') is not True:raise p.Rejected('native stage failed: '+name)
  if remaining()<=0 or size()>LIMIT:raise p.Rejected('whole diagnostic cap exceeded')
  return result
OUT.mkdir();record={'schema':1,'kind':'original_hardware_native_diagnostic','accepted':False,'physical_electrical_validation':False,'status':'incomplete','budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_cap_bytes':LIMIT,'source_commit':'5823d7a0d7fc3d1d520dd00f87bc5a42e413d04b','routing_executed':False,'helper_sha256':p.sha(Path(__file__))}
try:
 files=native_snapshot.capture();copy_bytes(files,OUT/'original');before=p.tree_hash(OUT/'original');board=OUT/'original/KiCad/devboard.kicad_pcb'
 record['original_hashes']=before;record['acquisition_receipt_sha256']=p.sha(ROOT/'.runs/licensed-acquisition-006-run-001/receipt.json');record['tools']=p.tool_manifest()
 copy_bytes({n:io.read_bytes(ROOT/n) for n in record['tools']['implementation_sha256']},OUT/'code')
 record['static_supported']=p.preflight(board) is not None
 job=BoundJob(OUT/'job',SECONDS,remaining);native=job.drc('original-drc',board);record['original_native']=native
 parity=job.out/'parity-input';shutil.copytree(board.parent,parity);expected=p.tree_hash(parity);parity_board=parity/board.name
 argv=[c.CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--schematic-parity','--exit-code-violations','--output',job.out/'parity-drc.json',parity_board]
 step=job.step('parity-drc',argv,allowed=(0,5));after=p.tree_hash(parity);p.check_drc_project(expected,after,board.name)
 p.save_json(job.out/'parity-drc-binding.json',{'source':str(board),'input':str(parity_board),'before':expected,'after':after,'saved':False})
 record['parity_native']=p.parse_report(job.out/'parity-drc.json',board.name)
 if (step['exit_code']==0)==bool(record['parity_native']['findings']):raise p.Rejected('parity exit/report mismatch')
 job.native('original-export','export',board,job.out/'original.dsn',job.out/'original-netclasses.json')
 job.native('original-metrics','metrics',board,job.out/'original-metrics.json');record['metrics']=f.read_json(job.out/'original-metrics.json')
 job.native('original-roundtrip','roundtrip',board,job.out/'roundtrip.kicad_pcb')
 original=sx.read(board);saved=sx.read(job.out/'roundtrip.kicad_pcb');record['native_saved_nonfill_ast_equal']=p.immutable(original)==p.immutable(saved)
 shell=p.transplant_routes(original,saved,protected=copy.deepcopy(p.routes(original)),policy='exact_non_uuid_lock_position_v2')
 record['original_shell_nonfill_ast_equal']=p.immutable(shell)==p.immutable(original)
 record['all_original_route_records_exact']=p.routes(shell)==p.routes(original)
 if not record['original_shell_nonfill_ast_equal'] or not record['all_original_route_records_exact']:raise p.Rejected('roundtrip original-shell preservation failed')
 record['status']='observed';record['native_routing_scope_accepted']=p.native_accepted(native);record['schematic_parity_findings']=len(f.read_json(job.out/'parity-drc.json')['schematic_parity'])
except (Exception,KeyboardInterrupt) as exc:
 record.update(status='failed',error=type(exc).__name__+': '+str(exc))
finally:
 if 'job' in globals():record['steps']=job.steps
 if 'before' in globals():record['original_preserved']=p.tree_hash(OUT/'original')==before;record['acquired_source_still_exact']=native_snapshot.capture()==files
 record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0,output_bytes=size())
 record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS and record['output_bytes']<=LIMIT
 if not record['within_budget'] or record.get('original_preserved') is not True or record.get('acquired_source_still_exact') is not True:record['status']='failed'
 p.save_json(OUT/'result.json',record)
 print(json.dumps({k:record.get(k) for k in ('status','error','native_routing_scope_accepted','schematic_parity_findings','metrics','wall_seconds','total_cpu_seconds','original_preserved','within_budget')}))
 raise SystemExit(0 if record['status']=='observed' else 2)
