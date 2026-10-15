"""Bounded pure independent reader plus callbacks-first final byte witnesses."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
specpath=ROOT/'.runs/ir-native-connected-repair-protocol-001.json';spec=f.read_json(specpath);specpin=p.sha(specpath);outerpath=ROOT/'.runs/ir-native-connected-repair-execution-001/execution.json';outer=f.read_json(outerpath);outerpin=p.sha(outerpath);actor=ROOT/'.runs/ir-native-connected-repair-001';classifier=ROOT/'.runs/ir-native-connected-classifier-001'
out=ROOT/'.runs/ir-native-connected-repair-readback-execution-001';out.mkdir()
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'.runs/read-ir-native-connected-repair-001.py')],cwd=out,log=out/'command.log',timeout=max(.001,9-(time.monotonic()-START)),max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=2*1024**3)
error=None;current=False;resultpath=ROOT/'.runs/ir-native-connected-repair-readback-001/result.json';result=f.read_json(resultpath) if resultpath.is_file() else None;resultpin=p.sha(resultpath) if result else None
try:
 assert p.tool_manifest()==spec['tools']
 assert p.sha(specpath)==specpin and p.sha(outerpath)==outerpin and p.sha(ROOT/'.runs/read-ir-native-connected-repair-001.py')==spec['reader_sha256']
 for n,d in spec['pins'].items():assert p.sha(ROOT/n)==d
 for n,d in spec['retained_material'].items():assert p.tree_hash(ROOT/n)==d
 assert f.evidence_inventory(actor)==outer['material']
 assert result and p.sha(resultpath)==resultpin and f.read_json(resultpath)==result
 current=True
except Exception as exc:error=type(exc).__name__+': '+str(exc)
wall,full=time.monotonic()-START,cpu()-CPU0;passed=bool(current and result['passed'] is True and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and not process['log_truncated'] and max(wall,full)<=10)
r=dict(schema=1,passed=passed,source_current=current,process=process,wall_seconds=wall,full_cpu_seconds=full,reader_publication_allowance_seconds=2,error=error,reader_sha256=spec['reader_sha256'],controller_sha256=p.sha(Path(__file__)),result_sha256=resultpin,outer_sha256=outerpin,protocol_sha256=specpin)
p.save_json(out/'execution.json',r);print(json.dumps({k:r[k] for k in ('passed','source_current','wall_seconds','full_cpu_seconds','error')}));raise SystemExit(0 if passed else 2)
