"""One finite revised-distribution qualification via the shared process runner."""
from pathlib import Path
import json,sys,os,time,resource
START=time.monotonic()
def cpu():return sum(v.ru_utime+v.ru_stime for v in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv
from autorouter.runner import run
base=ROOT/'.runs/install-distribution-native-010';protocol=base/'protocol.json';plan=f.read_json(protocol);pin=p.sha(protocol)
assert p.sha(Path(__file__))==plan['controller_sha256'];assert p.tool_manifest()['git_head']==plan['source_head']
assert plan['source_head']=='c3e7e8ef4dadce1f83f838322fb5d685ce3714ac' and p.sha(ROOT/'autorouter/gui.py')=='93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e'
assert Path(plan['output'])==ROOT/'.runs/runtime-directory-037'
def full180_current():
    prerequisite=plan['full_integration180']
    receipt=ROOT/'.runs/full-integration-180/execution.json';frozen=ROOT/'.runs/full-integration-180/protocol.json'
    suite=f.read_json(receipt);suite_plan=f.read_json(frozen)
    return (p.sha(receipt)==prerequisite['execution_sha256'] and p.sha(frozen)==prerequisite['protocol_sha256']
        and suite['passed'] is True and suite['sources_unchanged'] is True
        and suite['process']['status']=='success' and suite['process']['exit_code']==0
        and suite['process']['cleanup_complete'] is True and suite['process']['log_truncated'] is False
        and suite_plan['tools']['git_head']==plan['source_head']
        and suite_plan['source_sha256']['autorouter/gui.py']==prerequisite['gui_sha256']==p.sha(ROOT/'autorouter/gui.py'))
assert full180_current()
for name,digest in plan['source_files'].items():assert p.sha(ROOT/name)==digest
out=Path(plan['output']);assert not out.exists();folder=base/'enclosure';folder.mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith('KICAD_') and not k.startswith('GIT_') and k not in ('PYTHONPATH','PYTHONHOME')};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/install_smoke.py'),'--source-mode','distribution','--native-version','10.0.7','--output',str(out)],cwd=folder,env=env,log=folder/'command.log',timeout=615,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=1024**2)
p.save_json(folder/'process.json',process);receipt=out/'result.json';child=f.read_json(receipt) if receipt.is_file() else None
stable=full180_current() and p.sha(protocol)==pin and p.sha(Path(__file__))==plan['controller_sha256'] and p.tool_manifest()['git_head']==plan['source_head'] and all(p.sha(ROOT/name)==digest for name,digest in plan['source_files'].items())
passed=bool(child and child.get('passed') is True and child.get('source_installation_mode')=='distribution' and child.get('native_version')=='10.0.7' and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and stable and time.monotonic()-START<=600)
record=dict(schema=1,kind='actual-revised-distribution-native-smoke',passed=passed,accepted=False,project_complete=False,actual_GUI=False,protocol_sha256=pin,process=process,child_receipt=str(receipt),child_receipt_sha256=p.sha(receipt) if child else None,source_unchanged=stable,complete_wall_seconds=time.monotonic()-START,complete_full_CPU_seconds=cpu()-CPU0,scope='Actual fresh curated runtime/venv, doctor, native Route and check on owned fixture; no sixstage,GUI,cleanOS,relocation,Windows or publication claim.',reason=child.get('reason') if child else 'No child receipt')
p.save_json(base/'execution.json',record);print(json.dumps({k:v for k,v in record.items() if k!='process'}));raise SystemExit(0 if passed else 2)
