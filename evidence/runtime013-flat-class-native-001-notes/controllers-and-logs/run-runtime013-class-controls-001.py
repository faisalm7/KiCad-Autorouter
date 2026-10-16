"""Existing bounded process enclosure; no concurrent Native work."""
from pathlib import Path
import sys,os,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from autorouter.runner import run
case=ROOT/'.runs/runtime-directory-013';runtime=case/'runtime';out=runtime/'.runs/enclosure-class-controls-001';out.mkdir()
driver=ROOT/'.runs/qualify-runtime013-class-controls.py';pin=p.sha(driver)
process=run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(runtime/'.venv/bin/python'),'-B',str(driver),str(runtime),str(case/'setup.json')],cwd=runtime,log=out/'command.log',timeout=245,max_log_bytes=256*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=4*1024**3,env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}})
child=runtime/'.runs/class-controls-001/result.json';data=json.loads(child.read_bytes())if child.exists()else None
passed=bool(data and data.get('controls_passed')is True and process['status']=='success'and process['exit_code']==0 and process['cleanup_complete']is True and process['log_truncated']is False and pin==p.sha(driver))
p.save_json(out/'execution.json',dict(schema=1,accepted=False,controls_passed=passed,process=process,driver_sha256=pin,child_sha256=p.sha(child)if child.exists()else None))
print(json.dumps(dict(controls_passed=passed,status=process['status'],exit_code=process['exit_code'])))
raise SystemExit(0 if passed else 2)
