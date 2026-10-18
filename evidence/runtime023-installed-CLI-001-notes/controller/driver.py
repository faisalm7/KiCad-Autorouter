"""Bound the existing installed workflow qualifier; no replacement validator."""
import os, sys, time, resource, json
from pathlib import Path
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, provenance as pv
from autorouter.runner import run
base=ROOT/'.runs/runtime-directory-023';runtime=base/'runtime'
source=ROOT/'.runs/runtime-directory-019/source-matching/owned-four-copper-forced-inner.kicad_pcb'
source_pins=p.tree_hash(source.parent);tools=p.tool_manifest()
assert source_pins==json.loads((ROOT/'.runs/runtime-directory-020/cli-workflow-002-run/protocol.json').read_text())['source_hashes']
case=base/'cli-workflow-001-run';case.mkdir();mutable=runtime/'.runs';mutable.mkdir()
out=mutable/'production-delivery-001'
helper=ROOT/'scripts/qualify_runtime_workflow.py'
from autorouter import preferences as pref
preset=case/'settings.json';p.save_json(preset,pref.validate(dict(pref.DEFAULTS,seconds=420)));presetpin=p.sha(preset)
argv=[str(runtime/'.venv/bin/python'),'-B',str(helper),'--runtime',str(runtime),'--source',str(source),'--output',str(out),'--method','route','--settings',str(preset)]
protocol=dict(schema=1,source=str(source),source_hashes=source_pins,helper=str(helper),helper_sha256=p.sha(helper),runtime_manifest_sha256=p.sha(runtime/pv.MANIFEST),argv=argv,route_seconds=420,export_validation_seconds=120,settings_sha256=presetpin,external_bound_seconds=260,
 expected='Fresh installed4Cu six-stage delivery after explicit routing420/export120 budget split; protected whole4Cu regression. Each final needs own Native/fullSCH/class/original proof. No source changes, adapter comparison or actualGUI claim.',retained_failure='.runs/runtime-directory-020/cli-workflow-002-run')
p.save_json(case/'protocol.json',protocol)
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run(argv,cwd=case,env=env,log=case/'command.log',timeout=260,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=256*1024**2)
p.save_json(case/'process.json',process)
child=json.loads((out/'result.json').read_text()) if (out/'result.json').is_file() else None
stable=p.tree_hash(source.parent)==source_pins and p.tool_manifest()==tools and p.sha(helper)==protocol['helper_sha256'] and p.sha(preset)==presetpin and p.sha(runtime/pv.MANIFEST)==protocol['runtime_manifest_sha256']
passed=stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and child is not None and child['workflow_delivered'] is True
record=dict(schema=1,passed=passed,project_complete=False,actual_GUI=False,process=process,child_receipt_sha256=p.sha(out/'result.json') if child else None,protocol_sha256=p.sha(case/'protocol.json'),sources_unchanged=stable,whole_wall_seconds=time.monotonic()-START,whole_full_cpu_seconds=cpu()-CPU0,source_head=tools['git_head'])
p.save_json(case/'execution.json',record);print(json.dumps(record));raise SystemExit(0 if passed else 2)
