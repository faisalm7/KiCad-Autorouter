"""Bound the existing installed workflow qualifier; no replacement validator."""
import os, sys, time, resource, json
from pathlib import Path
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, provenance as pv
from autorouter.runner import run
base=ROOT/'.runs/runtime-directory-026';runtime=base/'runtime'
source=ROOT/'.data/boards/kicad-interf-u/interf_u.kicad_pcb'
source_pins=p.tree_hash(source.parent);tools=p.tool_manifest()
assert source_pins==json.loads((ROOT/'.runs/interf-installed023-comparison-001/protocol.json').read_text())['source_hashes']
case=ROOT/'.runs/runtime026-interf-prerequisite-001';case.mkdir();mutable=runtime/'.runs';mutable.mkdir(exist_ok=True)
out=mutable/'native7-interf-prerequisite-001'
helper=ROOT/'scripts/qualify_runtime_workflow.py'
from autorouter import preferences as pref
preset=case/'settings.json';p.save_json(preset,pref.validate(dict(pref.DEFAULTS,seconds=420)));presetpin=p.sha(preset)
argv=[str(runtime/'.venv/bin/python'),'-B',str(helper),'--runtime',str(runtime),'--source',str(source),'--output',str(out),'--method','route','--settings',str(preset)]
protocol=dict(schema=1,source=str(source),source_hashes=source_pins,helper=str(helper),helper_sha256=p.sha(helper),runtime_manifest_sha256=p.sha(runtime/pv.MANIFEST),argv=argv,route_seconds=420,export_validation_seconds=120,settings_sha256=presetpin,external_bound_seconds=260,
 expected='One fresh ordinary026/native7 corrected-standard B1 prerequisite on exposed licensed Interf. Existing seven-arm1000comparison is not repeated. Determine whether its solethermal failure persists before changing thermalworker/admission. Actual production Workflow/CLI/strictNative. If admitted, continue all six stages; otherwise preserve first actual failure with no fallback. No B0/B2/C comparison, qualitywin, sourcefix or GUI claim.',retained_failure='evidence/interf-installed023-comparison-001.json',attempts_maximum=1,administration_controller_sha256=p.sha(Path(__file__)),hypothesis='Native7 may preserve or remove the previously observed B1 solethermal failure. Do not port thermal recovery for this case unless a fresh solethermal Native outcome persists.',decision='If complete, retain normal7support and defer thermalport for this case. If solethermal, assess one bounded nonadmitting component prerequisite with existing mechanism. If otherfailure/unsupported/budget/cancel/stale, retain it and make no thermal/comparative inference.',source_rights='KiCad project CC-BY-SA-4.0; exact25file source and attribution/licenses match frozen023v4 inventory; exposeddevelopment, notholdout.',budget_scope='420routing/120export choices are retained inside qualifier hard240wholewall/fullCPU including15reserve, outer260wall. This is a strict prerequisite/control, not the old450method600delivery equal-budget comparison or a promise420usable routing seconds. If cap prevents Native, no thermal-cause conclusion.',controller_initial_syntax_failure='.runs/runtime026-interf-prerequisite-001-time.log;0.01wall0CPU;noNativeorprotocolcreated')
p.save_json(case/'protocol.json',protocol)
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run(argv,cwd=case,env=env,log=case/'command.log',timeout=260,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=256*1024**2)
p.save_json(case/'process.json',process)
child=json.loads((out/'result.json').read_text()) if (out/'result.json').is_file() else None
stable=p.tree_hash(source.parent)==source_pins and p.tool_manifest()==tools and p.sha(helper)==protocol['helper_sha256'] and p.sha(preset)==presetpin and p.sha(runtime/pv.MANIFEST)==protocol['runtime_manifest_sha256']
passed=stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and child is not None and child['workflow_delivered'] is True
record=dict(schema=1,passed=passed,project_complete=False,actual_GUI=False,process=process,child_receipt_sha256=p.sha(out/'result.json') if child else None,protocol_sha256=p.sha(case/'protocol.json'),sources_unchanged=stable,whole_wall_seconds=time.monotonic()-START,whole_full_cpu_seconds=cpu()-CPU0,source_head=tools['git_head'])
p.save_json(case/'execution.json',record);print(json.dumps(record));raise SystemExit(0 if passed else 2)
