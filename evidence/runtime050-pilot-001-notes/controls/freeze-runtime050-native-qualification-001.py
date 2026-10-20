"""Freeze fresh050 qualification using existing installer/query/Native workflow seams."""
from pathlib import Path
import copy,json,os,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv,gui
from autorouter.runner import run
from scripts import freeze_current_comparison as shared
HEAD='aa0072c6b3d8090de2603e5ecb42a95968fb873b'
MANIFEST='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
runtime=ROOT/'.runs/runtime-directory-050/runtime';out=ROOT/'.runs/runtime050-native-qualification-001'
assert pv.git_head(ROOT)==HEAD and p.sha(runtime/'runtime-distribution.json')==MANIFEST
assert shutil.disk_usage(ROOT).free>4*1024**3 and not out.exists()
full=f.read_json(ROOT/'.runs/full-integration-199/execution.json')
assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete'] and not full['process']['log_truncated']
prepared=f.read_json(ROOT/'.runs/runtime-directory-050/preparation.json')
assert prepared['prepared'] and prepared['source_head']==HEAD and prepared['manifest_sha256']==MANIFEST
out.mkdir(mode=0o700);query,query_pins=shared.query_runtime(runtime,out);tools=query['tools']
assert tools['source_provenance']['git_head']==HEAD and tools['source_provenance']['manifest_sha256']==MANIFEST
assert tools['kicad']=='10.0.7' and tools['source_provenance']['native_version']=='10.0.7'
doctor=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-m','autorouter','doctor'],cwd=runtime,env=gui.child_environment(),log=out/'doctor.json',timeout=90,max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=128*1024**2)
p.save_json(out/'doctor-process.json',doctor)
assert doctor['status']=='success' and doctor['exit_code']==0 and doctor['cleanup_complete'] and not doctor['log_truncated']
assert f.read_json(out/'doctor.json')['ready'] is True
prior=f.read_json(ROOT/'.runs/runtime049-native-qualification-001/frozen.json')
assert len(prior['protocols'])==6
templates={}
for row in prior['protocols']:
 path=Path(row['protocol']);assert p.sha(path)==row['protocol_sha256'];plan=f.read_json(path)
 assert plan['case']==row['case'] and plan['source_head']=='6e2357f975554478c2ba9fa35f18fdc3c1d194f9'
 assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
 templates[row['case']]=plan
npth=copy.deepcopy(templates['ordinary-alias2Cu']);npth.update(case='ordinary-npth2Cu',source=str(ROOT/'.runs/native7-npth-keepout-owned-source-001/source/owned1007-transport.kicad_pcb'),expected_counts=[0,0,6,0],expected_protected_count=1)
npth['source_hashes']=p.tree_hash(Path(npth['source']).parent)
npth['settings']['scope']='whole_board_unlocked_routing'
templates['ordinary-npth2Cu']=npth
encloser=ROOT/'.runs/enclose-runtime044-workflow-001.py';driver=ROOT/'scripts/qualify_runtime_workflow.py';rows=[]
for name in ['ordinary-npth2Cu',*[row['case'] for row in prior['protocols']]]:
 plan=copy.deepcopy(templates[name]);folder=out/name;folder.mkdir()
 settings=plan['settings'];p.save_json(folder/'settings.json',settings)
 output=runtime/'.runs'/(name+'-001');assert not output.exists()
 plan.update(schema=1,kind='runtime050-six-stage-route-or-improve-CLI',runtime=str(runtime),runtime_manifest_sha256=MANIFEST,source_head=HEAD,output=str(output),tools=tools,settings_sha256=p.sha(folder/'settings.json'),driver_sha256=p.sha(driver),enclosure_sha256=p.sha(encloser),scope='Fresh installed050 actual Request/Workflow/CliJob six-stage Native/fullSCH/original/protected delivery. Owned NPTH hole-blocked case plus six unchanged regression tasks; Native counts/warnings explicit. No actual GUI, comparative family/quality, Windows, cleanOS or release claim.')
 path=folder/'protocol.json';p.save_json(path,plan);rows.append(dict(case=name,method=plan['method'],protocol=str(path),protocol_sha256=p.sha(path)))
record=dict(schema=1,source_head=HEAD,runtime_manifest_sha256=MANIFEST,controller_sha256=p.sha(Path(__file__)),enclosure_sha256=p.sha(encloser),driver_sha256=p.sha(driver),protocols=rows,executed=False,scope='All seven protocols frozen before Native dispatch. Existing six-stage qualifier/shared bounded enclosure unchanged; each complete exit capped240wall/fullCPU. Prior049 plans supply task definitions only, no old result transfer. Native workers sequential.')
assert p.sha(runtime/'runtime-distribution.json')==MANIFEST and pv.git_head(ROOT)==HEAD
p.save_json(out/'frozen.json',record);print(json.dumps(record))
