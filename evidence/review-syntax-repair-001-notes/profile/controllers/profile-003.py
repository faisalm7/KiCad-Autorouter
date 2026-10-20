"""One bounded cProfile replay of the failed review, never reroute the cohort.

The product's own30s copy limit stays unchanged. Profiling costs are additional.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import fcntl,json,os,stat,sys
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime050 fresh install 001'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,floor_route as f
from autorouter.runner import run
from autorouter.gui import child_environment
base=ROOT/'.runs/runtime050-improve-review-profile-003';assert not base.exists();base.mkdir(mode=0o700)
manifest=runtime/'runtime-distribution.json';assert p.sha(manifest)=='8fdf819606e2345b932139f1c16c330825fd8634caef1b611b5e105b97be22a4'
producer=runtime/'.runs/native7-method-runtime050-default-improve-development-001-ir-obstacle-Cimprove'
failed=f.read_json(producer/'review.process.json');argv=failed['argv'];assert argv[3:5]==['autorouter','review-copy']
receipt=Path(argv[5]);data=f.read_json(receipt);source=Path(data['source']);hashes=io.inventory(source.parent)
assert hashes==data['source_hashes'] and data['accepted'] is True and len(data['trials'])==18
assert failed['exit_code']==2 and f.read_json(producer/'review.log')['reason']=='review copy exceeded 30-second wall or full CPU ceiling'
tool_manifest=p.tool_manifest();receipt_pin=p.sha(receipt)
command=[str(runtime/'.venv/bin/python'),'-B','-m','cProfile','-o',str(base/'review.pstats'),'-m',*argv[3:-1],str(base/'review')]
p.save_json(base/'protocol.json',dict(schema=1,kind='single-failed050-Improve-review-cProfile-diagnostic-v1',runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),tools=tool_manifest,source=str(source),source_hashes=hashes,receipt=str(receipt),receipt_sha256=receipt_pin,actual_failed_process_sha256=p.sha(producer/'review.process.json'),original_failed_output_untouched=argv[-1],argv=command,outer_wall_seconds=120,product_copy_wall_CPU_seconds=30,profile_overhead_not_normal_runtime=True,no_routing_or_cohort_rerun=True,prior_launcher_prelaunch_disk_limit=str(ROOT/'.runs/runtime050-improve-review-profile-001/execution.json'),disk_guard_scope='fresh diagnostic output only; runtime imported explicitly by controlled PYTHONPATH',project_complete=False))
with open(ROOT/'.runs/quality-experiment.lock','r+') as lane:
    info=os.fstat(lane.fileno());assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
    fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
    process=run(command,cwd=base,env={**child_environment(),'PYTHONPATH':str(runtime)},log=base/'command.log',timeout=max(.001,120-(time.monotonic()-START)),max_log_bytes=128*1024,max_group_rss_bytes=2*1024**3,max_workdir_bytes=128*1024**2)
stable=io.inventory(source.parent)==hashes and p.sha(receipt)==receipt_pin and p.tool_manifest()==tool_manifest
p.save_json(base/'execution.json',dict(schema=1,process=process,wall_seconds=time.monotonic()-START,full_CPU_seconds=cpu()-CPU0,inputs_tools_unchanged=stable,profile_exists=(base/'review.pstats').is_file(),normal_workflow_success=False,cohort_outcome_changed=False,project_complete=False,controller_sha256=p.sha(Path(__file__))))
print(json.dumps(dict(status=process['status'],exit_code=process['exit_code'],inputs_tools_unchanged=stable,profile_exists=(base/'review.pstats').is_file(),scope='Additional instrumented diagnostic; not comparative cost or a repaired workflow.')))
raise SystemExit(0 if stable and (base/'review.pstats').is_file() and process['cleanup_complete'] is True else 2)
