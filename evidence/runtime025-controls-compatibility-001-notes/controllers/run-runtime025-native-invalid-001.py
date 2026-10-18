"""Enclose two Native negatives using the existing sequential process runner."""
from pathlib import Path
import sys,os,time,resource,json
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv
from autorouter.runner import run
base=ROOT/'.runs/runtime-directory-025';runtime=base/'runtime';case=base/'native-invalid-001-enclosure';case.mkdir()
output=runtime/'.runs/native-invalid-001';helper=ROOT/'.runs/qualify-runtime025-native-invalid-001.py'
argv=[str(runtime/'.venv/bin/python'),'-B',str(helper),'--runtime',str(runtime),'--whole-delivery',str(runtime/'.runs/production-delivery-001'),'--partial-delivery',str(runtime/'.runs/partial-delivery-001'),'--output',str(output)]
protocol=dict(schema=1,argv=argv,helper_sha256=p.sha(helper),runtime_manifest_sha256=p.sha(runtime/pv.MANIFEST),external_wall_full_CPU_seconds=180,scope='Two fresh invalid candidates after actual ordinary1007 whole/partial six-stage delivery; Native short and1nm protected-width refusal. No engine, GUI, accepted route/export or broad version/family claim.')
p.save_json(case/'protocol.json',protocol)
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run(argv,cwd=case,env=env,log=case/'command.log',timeout=max(.001,180-(time.monotonic()-START)),max_log_bytes=1024**2,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
p.save_json(case/'process.json',process)
child=json.loads((output/'result.json').read_text()) if(output/'result.json').is_file() else None
stable=p.sha(helper)==protocol['helper_sha256'] and p.sha(runtime/pv.MANIFEST)==protocol['runtime_manifest_sha256']
record=dict(schema=1,passed=False,accepted=False,project_complete=False,actual_GUI=False,process=process,child_sha256=p.sha(output/'result.json') if child else None,stable=stable,whole_wall_seconds=time.monotonic()-START,whole_full_CPU_seconds=cpu()-CPU0,protocol_sha256=p.sha(case/'protocol.json'))
record['passed']=bool(stable and child is not None and child.get('control_passed') is True and child.get('status')=='completed' and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and max(record['whole_wall_seconds'],record['whole_full_CPU_seconds'])<=180)
p.save_json(case/'execution.json',record);print(json.dumps(record));raise SystemExit(0 if record['passed'] else 2)
