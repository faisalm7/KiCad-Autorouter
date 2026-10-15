from pathlib import Path
import time,resource,sys,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
out=ROOT/'.runs/four-cu-class-targeted-002';out.mkdir()
code={str(x):p.sha(x) for x in [*ROOT.glob('autorouter/*.py'),*ROOT.glob('tests/test_netclass*.py'),ROOT/'tests/test_four_copper_classes.py',ROOT/'experiments/four_copper_class_transport_v1/fixture.py']}
mods=['tests.test_four_copper_classes','tests.test_netclass','tests.test_netclass_parent_policy','tests.test_netclass_native','tests.test_netclass_pipeline','tests.test_netclass_parent_pipeline','tests.test_netclass_unused','tests.test_literal_composite','tests.test_native_class_readback']
bootstrap='import sys,unittest;sys.dont_write_bytecode=True;sys.path[:0]='+repr([str(ROOT),str(ROOT/'tests')])+';unittest.main(module=None,argv='+repr(['unittest','-v',*mods])+')'
proc=run([str(ROOT/'.venv/bin/python'),'-B','-c',bootstrap],cwd=out,log=out/'command.log',timeout=120,max_log_bytes=256*1024,max_workdir_bytes=8*1024**2,max_group_rss_bytes=1024**3)
record=dict(process=proc,wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,code_sha256=code,log_sha256=p.sha(out/'command.log'),source_unchanged=code=={n:p.sha(Path(n)) for n in code},scope='Four-copper source/native/export class and crossbinding software controls plus existing two-copper guards. Native support unqualified. Initial001 wrapper authoring failure preserved separately, costs unavailable.')
p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ['wall_seconds','full_cpu_seconds','source_unchanged']}));print(json.dumps({k:proc[k] for k in ['status','exit_code','cleanup_complete']}));raise SystemExit(0 if proc['status']=='success' and proc['exit_code']==0 and record['source_unchanged'] else 2)
