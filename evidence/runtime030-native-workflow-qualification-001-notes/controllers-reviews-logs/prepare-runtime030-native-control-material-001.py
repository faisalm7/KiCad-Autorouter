"""Prepare small owned control material once; no Native invocation or benchmark."""
from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv
from autorouter.runner import run
from autorouter.gui import child_environment
assert f.read_json(ROOT/'.runs/full-integration-172/execution.json')['passed'] is True
assert f.read_json(ROOT/'.runs/install-distribution-native-003/execution.json')['passed'] is True
runtime=ROOT/'.runs/runtime-directory-030/runtime';manifest=runtime/pv.MANIFEST;distribution=f.read_json(manifest)
assert distribution['build_source']['git_head']=='a658e62c71204f7242a66c695f22a1b3e2263482'
base=ROOT/'.runs/runtime030-native-controls-preparation-001';base.mkdir()
scripts=('qualify-comparison-delivery-001.py','qualify-runtime030-comparison-native-invalid-001.py','qualify-native7-comparison-route-child-001.py')
pins={}
for name in scripts:
 source=ROOT/'.runs'/name;target=runtime/'.runs'/name;assert not target.exists();shutil.copyfile(source,target);pins[name]=p.sha(target);assert pins[name]==p.sha(source)
assert pins[scripts[0]]=='c15417b86dbb4db66f0b318db5adf2b1b8298b3d328c20afdbf5f5d537d563a6'
assert pins[scripts[1]]=='e719d4198d6d65aa4351e85ab61b4d92dc29260b25a9af09f60f97b867ae23c1'
code='import sys,json;sys.path.insert(0,sys.argv[1]);from autorouter import pipeline as p;print(json.dumps(p.tool_manifest()))'
process=run([str(runtime/'.venv/bin/python'),'-B','-c',code,str(runtime)],cwd=base,env=child_environment(),log=base/'tools.json',timeout=20,max_log_bytes=128*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=1024**2)
p.save_json(base/'process.json',process);assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
tools=f.read_json(base/'tools.json');assert tools['git_head']==distribution['build_source']['git_head'] and tools['source_provenance']['manifest_sha256']==p.sha(manifest) and tools['kicad']=='10.0.7'
source=ROOT/'.runs/task-copper-fixed-alias-native-004/source';fixture=p.tree_hash(source);assert len(fixture)==4
texts={name:(source/name).read_bytes().decode('utf-8') for name in fixture};assert all(p.sha(source/name)==pin for name,pin in fixture.items())
p.save_json(base/'material.json',dict(runtime=str(runtime),source_head=tools['git_head'],runtime_manifest_sha256=p.sha(manifest),runtime_tools=tools,controller_pins=pins,fixture_source=str(source),fixture_files=texts,fixture_sha256=fixture))
print(json.dumps({'prepared':True,'Native_executed':False,'material':str(base/'material.json'),'material_sha256':p.sha(base/'material.json')}))
