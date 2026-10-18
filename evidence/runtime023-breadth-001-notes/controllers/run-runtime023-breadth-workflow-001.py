"""Two finite current installed coverage checks with existing six-stage helper."""
from pathlib import Path
import argparse,json,os,resource,sys,time
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,preferences as pref
from autorouter.runner import run
ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['NUS_partial','Sonde_whole'],required=True);a=ap.parse_args()
base=ROOT/'.runs/runtime-directory-023';runtime=base/'runtime';tools=p.tool_manifest()
if a.case=='NUS_partial':
 reference=json.loads((ROOT/'.runs/task-copper-fixed-nus-native-001/route/result.json').read_text());source=Path(reference['source']);pins=reference['source_hashes'];assert reference['accepted'] is True and len(pins)==8
 settings=pref.validate(dict(pref.DEFAULTS,seconds=120,scope='partial_completion'))
 rights='CERN-OHL-P-2.0 creatorREADME/License pinned in sourceinventory; thirdpartyfootprint/model/asset origin closure remains uncertain. All raw CAD/DSN/SES/XY/nativepayloads stay local; publish only sanitized current result metadata.'
 expected_protected=47;expected_pcb='a8e69c14ceec9dd0954c3027cc89ca6bbb9c0b0ec3aeede5feacfdd47736f362'
else:
 source=ROOT/'.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb';manifest=json.loads((ROOT/'data/sources.json').read_text());pins={str(Path(x['destination']).relative_to('boards/kicad-sonde-xilinx')):x['sha256']for x in manifest['files']if x.get('project_id')=='kicad-sonde-xilinx'};assert len(pins)==16
 settings=pref.validate(dict(pref.DEFAULTS,seconds=120));rights='CC-BY-SA-4.0 acquiredKiCadrevision69cafb907ebc09e7722a2a464b1d466fc2e3608d and inheritedTuxnotices; exact sourceinventory/data manifest retained.';expected_protected=0;expected_pcb='d0dee876715fcdd3f656dd6a77cc1141c39bec4d6f8492a3784d38edd6b9a998'
assert p.tree_hash(source.parent)==pins and pins[source.name]==expected_pcb
case=base/(a.case+'-workflow-001-run');case.mkdir();preset=case/'settings.json';p.save_json(preset,settings);presetpin=p.sha(preset);out=runtime/'.runs'/('breadth-'+a.case+'-delivery-001')
helper=ROOT/'scripts/qualify_runtime_workflow.py';helperpin=p.sha(helper)
argv=[str(runtime/'.venv/bin/python'),'-B',str(helper),'--runtime',str(runtime),'--source',str(source),'--output',str(out),'--method','route','--settings',str(preset)]
p.save_json(case/'protocol.json',dict(schema=1,source=str(source),source_hashes=pins,settings=settings,settings_sha256=presetpin,argv=argv,helper_sha256=helperpin,runtime_manifest_sha256=p.sha(runtime/pv.MANIFEST),route_seconds=120,whole_delivery_wall_fullCPU_seconds=240,outer_watchdog_seconds=260,rights=rights,expected_protected_records=expected_protected,scope='One fresh installed Native sixstage qualification on an already exposed declaredfamily. No source/profile tuning or comparative/speed/electrical/independence/GUI claim; NUSsource already0opens. Preserve refusal/overrun/warnings and every final own proof.'))
env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run(argv,cwd=case,env=env,log=case/'command.log',timeout=260,max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=256*1024**2);p.save_json(case/'process.json',process)
child=json.loads((out/'result.json').read_text())if(out/'result.json').is_file()else None
stable=p.tree_hash(source.parent)==pins and p.tool_manifest()==tools and p.sha(helper)==helperpin and p.sha(preset)==presetpin
passed=stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and child is not None and child['workflow_delivered'] is True
record=dict(schema=1,case=a.case,passed=passed,project_complete=False,actual_GUI=False,process=process,child_receipt=str(out/'result.json'),child_receipt_sha256=p.sha(out/'result.json')if child else None,sources_unchanged=stable,sampled_wall_seconds=time.monotonic()-START,sampled_fullCPU_seconds=cpu()-CPU0,source_runtime_head=json.loads((base/'setup.json').read_text())['source_head'],administration_head=tools['git_head'],rights=rights)
if max(record['sampled_wall_seconds'],record['sampled_fullCPU_seconds'])>240:record['passed']=False
p.save_json(case/'execution.json',record);print(json.dumps({k:v for k,v in record.items()if k!='process'}));raise SystemExit(0 if record['passed'] else 2)
