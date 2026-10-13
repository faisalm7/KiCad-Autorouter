"""Bounded original-project observations using shared native/process validators.

No engine, routing, source mutation, production admission or physical approval.
The Devobordo observations already exist; do not rerun them to resume work.
"""
from pathlib import Path
import argparse,copy,fcntl,hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,sexpr as sx,floor_route as f,placement_clearance as io
from autorouter.runner import run
from experiments.placement_handoff_native_v1.driver import copy_bytes
LIMIT=20*1024**2;SECONDS=90
CASES={'ardujoy-c64':('v4','Ardujoy_HW/Ardujoy_HW.kicad_pcb','1b63471d9726fb6a38f8544ca73ebf10c7f19820','.runs/licensed-acquisition-007-run-001/receipt.json')}

def route_records(tree):
    result={}
    for row in p.routes(tree):
        identity=sx.one(row,'uuid')
        if identity is None or len(identity)!=2 or identity[1] in result:raise p.Rejected('missing or duplicated route UUID')
        result[identity[1]]=row
    return result

def experiment(project,output,*,run_native=False):
    if run_native is not True or project not in CASES:raise p.Rejected('explicit fixed source and --run-native required')
    started=time.monotonic();cpu0=time.process_time()+f.child_cpu();out=Path(output).absolute()
    if not out.is_relative_to(ROOT/'.runs') or '..' in out.parts or any(x.is_symlink() for x in (out,*out.parents)):raise p.Rejected('fresh canonical checkout output required')
    out.mkdir();version,relative,commit,acquisition=CASES[project]
    def remaining():return min(SECONDS-(time.monotonic()-started),SECONDS-(time.process_time()+f.child_cpu()-cpu0))
    def size():return sum(len(x) for x in io.inventory(out,contents=True,max_bytes=LIMIT,max_files=2048,max_entries=4096).values())
    class BoundJob(f.FloorJob):
        def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
            if remaining()<=0:raise p.Rejected('whole original diagnostic budget exhausted')
            actual=[str(a) for a in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
            step=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=min(30,remaining()),env=self.env,max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
            step['name']=name;self.steps.append(step);p.save_json(self.out/(name+'-process.json'),step)
            if step['status'] not in ('success','nonzero_exit') or step['exit_code'] not in allowed or step.get('cleanup_complete') is not True:raise p.Rejected('native stage failed: '+name)
            if remaining()<=0 or size()>LIMIT:raise p.Rejected('whole original diagnostic cap exceeded')
            return step
    record={'schema':1,'kind':'original_hardware_native_diagnostic','project':project,'accepted':False,'physical_electrical_validation':False,'status':'incomplete','budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'output_cap_bytes':LIMIT,'source_commit':commit,'routing_executed':False,'helper_sha256':p.sha(Path(__file__))}
    before=files=job=None
    try:
        from importlib import import_module
        snapshot=import_module('experiments.licensed_acquisition_'+version+'.native_snapshot')
        files=snapshot.capture();copy_bytes(files,out/'original');before=p.tree_hash(out/'original');board=out/'original'/relative
        record.update(original_hashes=before,acquisition_receipt_sha256=p.sha(ROOT/acquisition),tools=p.tool_manifest())
        code={n:io.read_bytes(ROOT/n) for n in record['tools']['implementation_sha256']}
        for name,raw in code.items():
            committed=subprocess.run(['git','show',record['tools']['git_head']+':'+name],cwd=ROOT,capture_output=True,check=True,timeout=min(3,remaining())).stdout
            if raw!=committed:raise p.Rejected('commit exact native implementation before observations')
        copy_bytes(code,out/'code');record['static_supported']=p.preflight(board) is not None
        job=BoundJob(out/'job',SECONDS,remaining);record['original_native']=job.drc('original-drc',board)
        record['parity_native']=job.drc('parity-drc',board,schematic_parity=True)
        job.native('original-export','export',board,job.out/'original.dsn',job.out/'original-netclasses.json')
        job.native('original-metrics','metrics',board,job.out/'original-metrics.json');record['metrics']=f.read_json(job.out/'original-metrics.json')
        job.native('original-roundtrip','roundtrip',board,job.out/'roundtrip.kicad_pcb')
        original=sx.read(board);saved=sx.read(job.out/'roundtrip.kicad_pcb');record['native_saved_nonfill_ast_equal']=p.immutable(original)==p.immutable(saved)
        shell=p.transplant_routes(original,saved,protected=copy.deepcopy(p.routes(original)),policy='exact_non_uuid_lock_position_v2')
        record['original_shell_nonfill_ast_equal']=p.immutable(shell)==p.immutable(original)
        record['all_original_route_records_exact']=route_records(shell)==route_records(original)
        if not record['original_shell_nonfill_ast_equal'] or not record['all_original_route_records_exact']:raise p.Rejected('roundtrip original-shell preservation failed')
        record.update(status='observed',native_routing_scope_accepted=p.native_accepted(record['original_native']),schematic_parity_findings=len(f.read_json(job.out/'parity-drc.json')['schematic_parity']))
    except (Exception,KeyboardInterrupt) as exc:record.update(status='failed',error=type(exc).__name__+': '+str(exc))
    finally:
        if job is not None:record['steps']=job.steps
        if before is not None:
            record.update(original_preserved=p.tree_hash(out/'original')==before,acquired_source_still_exact=snapshot.capture()==files)
        record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0,output_bytes=size())
        record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS and record['output_bytes']<=LIMIT
        if not record['within_budget'] or record.get('original_preserved') is not True or record.get('acquired_source_still_exact') is not True:record['status']='failed'
        p.save_json(out/'result.json',record)
    return record

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=list(CASES),required=True);parser.add_argument('--output',required=True);parser.add_argument('--run-native',action='store_true');args=parser.parse_args()
    with (ROOT/'.runs/experiment.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.project,args.output,run_native=args.run_native)
    print(json.dumps({k:result.get(k) for k in ('status','error','native_routing_scope_accepted','schematic_parity_findings','metrics','wall_seconds','total_cpu_seconds','within_budget')}));return 0 if result['status']=='observed' else 2
if __name__=='__main__':raise SystemExit(main())
