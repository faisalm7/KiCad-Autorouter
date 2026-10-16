from pathlib import Path
import sys,os,time,resource,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv
from autorouter.runner import run
from experiments.four_copper_pour_support_v1 import fixture
from autorouter import sexpr as sx,netclass as nc
start=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
cpu0=cpu();case=ROOT/'.runs/runtime-directory-006';case.mkdir();runtime=case/'runtime';processes=[]
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
for name,argv in [('build',[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/prepare_runtime.py'),'--output',str(runtime),'--copy-local-engine']),('venv',[str(ROOT/'.venv/bin/python'),'-B','-m','venv','--copies','--without-pip',str(runtime/'.venv')])]:
 proc=run(argv,cwd=case,log=case/(name+'.log'),timeout=90,max_log_bytes=64*1024,max_workdir_bytes=256*1024**2,max_group_rss_bytes=1024**3,env=env);processes.append(proc)
 assert proc['status']=='success' and proc['exit_code']==0 and proc['cleanup_complete'] is True
source=case/'source';source.mkdir()
files=fixture.files();boardname=fixture.STEM+'.kicad_pcb';canonical=sx.parse(files[boardname].decode())
aliased=sx.parse(files[boardname].decode());display={'9':'F.Adhesive','11':'B.Adhesive','5':'F.Silkscreen','7':'B.Silkscreen','17':'User.Drawings','19':'User.Comments','21':'User.Eco1','23':'User.Eco2','31':'F.Courtyard','29':'B.Courtyard'}
added=[]
for row in sx.one(aliased,'layers')[1:]:
 if row[0]in display:
  assert len(row)==3 and row[2]=='user';row.append(json.dumps(display[row[0]]));added.append(row[0])
assert added and nc.four_copper_source_layers(aliased)==list(nc.FOUR_COPPER_NAMES)
restored=sx.parse(sx.dump(aliased))
for row in sx.one(restored,'layers')[1:]:
 if row[0]in added:row.pop()
assert restored==canonical
files[boardname]=(sx.dump(aliased)+'\n').encode()
for name,raw in files.items():(source/name).write_bytes(raw)
assert len(p.routes(aliased))==10 and all(p.locked(route)for route in p.routes(aliased));p.preflight(source/boardname)
invalid=case/'invalid-physical-layer';invalid.mkdir()
bad=sx.parse(sx.dump(aliased));table=sx.one(bad,'layers');table[2][0],table[3][0]=table[3][0],table[2][0]
for name,raw in files.items():(invalid/name).write_bytes((sx.dump(bad)+'\n').encode()if name==boardname else raw)
try:p.preflight(invalid/boardname);raise AssertionError('Swapped physical layer identity unexpectedly passed.')
except p.Rejected as exc:invalid_reason=str(exc)

(runtime/'.runs').mkdir()
record=dict(schema=1,prepared=True,native_or_JVM=False,source_head=pv.git_head(ROOT),runtime=str(runtime),source=str(source/boardname),source_hashes=p.tree_hash(source),manifest_sha256=p.sha(runtime/pv.MANIFEST),builder_sha256=p.sha(ROOT/'scripts/prepare_runtime.py'),processes=processes,wall_seconds=time.monotonic()-start,full_CPU_seconds=cpu()-cpu0,pour_source_form='omitted-net-explicit-island0',noncopper_display_layers=added,canonical_factory_sha256={k:__import__('hashlib').sha256(v).hexdigest()for k,v in fixture.files().items()},invalid_physical_source=str(invalid/boardname),invalid_physical_reason=invalid_reason,required_new_inner_nets=['ROUTE'],required_protected_routes=10,qualification='Actual curated local Mac runtime, copied cachedJAR and fresh no-pip venv, owned externalfullSCHfixture. Native/GUI qualification pending. No downloads/AIaccount/packagepublication.')
p.save_json(case/'setup.json',record);print(json.dumps({k:record[k] for k in ['prepared','source_head','wall_seconds','full_CPU_seconds']}))
