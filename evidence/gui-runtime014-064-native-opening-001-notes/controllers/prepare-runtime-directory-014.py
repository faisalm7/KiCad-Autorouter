"""Reuse the curated builder/runner for one frozen ordinary-class integration."""
from pathlib import Path
import json, os, resource, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,sexpr as sx
from autorouter.runner import run
from experiments.flat_class_route_v1 import fixture
start=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
cpu0=cpu();tools=p.tool_manifest();case=ROOT/'.runs/runtime-directory-014';case.mkdir();runtime=case/'runtime';processes=[]
env={k:v for k,v in os.environ.items()if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
for name,argv in [('build',[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/prepare_runtime.py'),'--output',str(runtime),'--copy-local-engine']),('venv',[str(ROOT/'.venv/bin/python'),'-B','-m','venv','--copies','--without-pip',str(runtime/'.venv')])]:
 proc=run(argv,cwd=case,log=case/(name+'.log'),timeout=90,max_log_bytes=64*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=1024**3,env=env);processes.append(proc)
 assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete']is True
sources={}
for name,options in [('matching',{}),('clean-fields',{'clean_fields':True}),('mismatch',{'mismatch':True})]:
 folder=case/('source-'+name);folder.mkdir();packet=fixture.files(**options)
 for filename,raw in packet.items():(folder/filename).write_bytes(raw)
 board=folder/(fixture.STEM+'.kicad_pcb');tree=sx.read(board)
 assert len(p.routes(tree))==10 and all(p.locked(r)for r in p.routes(tree))
 p.preflight(board,class_context='native-route-flat-classes-v1')
 sources[name]=dict(board=str(board),source_hashes=p.tree_hash(folder),options=options,protected_routes=10)
# Create the existing owned no-class source afresh for the changed plain API path.
from experiments.stronger_incumbent_v1 import global_width_fixture as plain
folder=case/'source-plain';folder.mkdir()
for filename,raw in plain.files().items():(folder/filename).write_bytes(raw)
board=folder/(plain.STEM+'.kicad_pcb');p.preflight(board)
prior=json.loads((ROOT/'.runs/runtime-directory-003/setup.json').read_text())
assert p.tree_hash(folder)==prior['source_hashes']
sources['plain']=dict(board=str(board),source_hashes=p.tree_hash(folder),options={},protected_routes=1)
old=json.loads((ROOT/'.runs/runtime-directory-013/setup.json').read_text());prior_manifest=json.loads((Path(old['runtime'])/'runtime-distribution.json').read_text());new_manifest=json.loads((runtime/'runtime-distribution.json').read_text());a=prior_manifest['build_source']['files_sha256'];b=new_manifest['build_source']['files_sha256'];modules_a={n:v for n,v in a.items()if n.startswith('autorouter/')};modules_b={n:v for n,v in b.items()if n.startswith('autorouter/')};assert set(modules_a)==set(modules_b)and len(modules_a)==44;changed=[n for n in modules_b if modules_a[n]!=modules_b[n]];assert changed==['autorouter/gui.py'],changed
(runtime/'.runs').mkdir()
assert p.tool_manifest()==tools
p.save_json(case/'setup.json',dict(schema=1,prepared=True,native_or_JVM=False,source_head=tools['git_head'],tools=tools,runtime=str(runtime),sources=sources,
 manifest_sha256=p.sha(runtime/pv.MANIFEST),builder_sha256=p.sha(ROOT/'scripts/prepare_runtime.py'),fixture_sha256=p.sha(ROOT/'experiments/flat_class_route_v1/fixture.py'),processes=processes,
 wall_seconds=time.monotonic()-start,full_CPU_seconds=cpu()-cpu0,qualification='New source-bound curated Mac runtime; owned matching/mismatch/clean-field variants share one exposed family. Fresh no-pip copied interpreter and cachedJAR, no external download/publication. Actual Native/GUI pending.'))
print(json.dumps(dict(prepared=True,source_head=tools['git_head'],wall_seconds=time.monotonic()-start,full_CPU_seconds=cpu()-cpu0)))
