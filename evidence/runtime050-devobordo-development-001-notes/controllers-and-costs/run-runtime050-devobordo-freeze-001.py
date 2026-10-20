"""One bounded setup invocation through existing shared runner; no arm dispatch."""
from pathlib import Path
import fcntl,json,os,sys,time,resource
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from autorouter.gui import child_environment
start=time.monotonic();cpu0=sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
head='1dadb9d380c33f8810fb0fa9494931af78bc08be'
child=ROOT/'.runs/freeze-runtime050-devobordo-followup-001.py'
assert p.sha(child)=='2d4960475d419d72d5aea50b65e6dbfaed0dd05afed47868e90007de8fa728d6'
out=ROOT/'.runs/runtime050-devobordo-freeze-enclosure-001';out.mkdir(mode=0o700)
with (ROOT/'.runs/quality-experiment.lock').open('r+') as lane:
 fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
 process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(child),'--administration-head',head],cwd=out,env=child_environment(),log=out/'command.log',timeout=115,max_log_bytes=512*1024,max_group_rss_bytes=2*1024**3,max_workdir_bytes=2*1024**2)
 p.save_json(out/'process.json',process)
 wall=time.monotonic()-start;cpu=sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))-cpu0
 frozen=ROOT/'.runs/runtime050-devobordo-development-followup-001/frozen-children.json'
 passed=process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] and max(wall,cpu)<120 and frozen.is_file()
 record=dict(schema=1,setup_passed=passed,actual_GUI=False,Native_routing_or_DRC_executed=False,project_complete=False,administration_head=head,controller_sha256=p.sha(child),process=process,frozen_children_sha256=p.sha(frozen) if frozen.is_file() else None,sampled_wall_seconds=wall,sampled_full_CPU_seconds=cpu,external_complete_exit_required=True,scope='One setup invocation,115s existing shared process timeout within120s setup acceptance.2MiB workdir guard covers enclosure logs only; frozen metadata sibling retains its own guards. No arms run. Parent/child CPU samples overlap external exit and are not additive.')
 p.save_json(out/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if passed else 2)
