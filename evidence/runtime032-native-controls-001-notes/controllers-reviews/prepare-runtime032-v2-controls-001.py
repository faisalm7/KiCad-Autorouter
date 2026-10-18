"""One material preparation for explicit v2 functional controls; no Native invocation."""
from pathlib import Path
import sys,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv
from autorouter.runner import run
from autorouter.gui import child_environment
assert f.read_json(ROOT/'.runs/full-integration-175/execution.json')['passed']
assert f.read_json(ROOT/'.runs/install-distribution-native-005/execution.json')['passed']
runtime=ROOT/'.runs/runtime-directory-032/runtime';manifest=runtime/pv.MANIFEST;distribution=f.read_json(manifest)
base=ROOT/'.runs/runtime032-v2-controls-preparation-001';base.mkdir()
names=('qualify-comparison-v2-delivery-001.py','qualify-comparison-v2-route-child-001.py','cancel-comparison-v2-engine-001.py','qualify-comparison-v2-native-invalid-001.py','owned-child-path-observer-001.py')
pins={}
for name in names:
 source=ROOT/'.runs'/name;target=runtime/'.runs'/name;assert not target.exists();shutil.copyfile(source,target);pins[name]=p.sha(target);assert pins[name]==p.sha(source)
code='import sys,json;sys.path.insert(0,sys.argv[1]);from autorouter import pipeline as p;print(json.dumps(p.tool_manifest()))'
process=run([str(runtime/'.venv/bin/python'),'-B','-c',code,str(runtime)],cwd=base,env=child_environment(),log=base/'tools.json',timeout=20,max_log_bytes=128*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=1024**2)
p.save_json(base/'process.json',process);assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
tools=f.read_json(base/'tools.json');assert tools['git_head']==distribution['build_source']['git_head'] and tools['source_provenance']['manifest_sha256']==p.sha(manifest) and tools['kicad']=='10.0.7' and tools['comparison_route_policy']=='selected-native7-fixed-comparison-v2'
old=f.read_json(ROOT/'.runs/runtime030-native-controls-preparation-001/material.json');source=Path(old['fixture_source']);assert p.tree_hash(source)==old['fixture_sha256']
p.save_json(base/'material.json',dict(runtime=str(runtime),source_head=tools['git_head'],runtime_manifest_sha256=p.sha(manifest),runtime_tools=tools,controller_pins=pins,fixture_source=str(source),fixture_files=old['fixture_files'],fixture_sha256=old['fixture_sha256']))
print(json.dumps(dict(prepared=True,Native_executed=False,material=str(base/'material.json'),sha256=p.sha(base/'material.json'))))
