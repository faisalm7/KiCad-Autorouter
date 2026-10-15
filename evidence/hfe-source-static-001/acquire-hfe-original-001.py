"""Missing pinned HFE originals only; no scripts, router, models or native execution."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from experiments.licensed_acquisition_v1 import fetch as shared
O=R/'.runs/hfe-original-acquisition-001';O.mkdir();(O/'raw').mkdir();(O/'source').mkdir();owner={};h.capture_destination(owner,O)
T=R/'.runs/new-family-prospect-004';TPIN='933be7e184c7bb0a02ce392e1f6fdd601e2320323d56b26e0655d2561ed11c01';assert p.sha(T/'009-hfe-tree.json')==TPIN
tree=f.read_json(T/'009-hfe-tree.json');commit='7be61154def1890aa66368b3385ad8661447d52f'
rows=[]
for n in ['transistor-hfe-measurement-circuit.kicad_pcb','transistor-hfe-measurement-circuit.kicad_sch','cc-component.kicad_sch']:
 a=next(x for x in tree['tree'] if x['path']==n);assert a['mode']=='100644' and a['type']=='blob'
 rows.append(dict(source_path=n,bytes=a['size'],git_blob_sha1=a['sha'],raw_url='https://raw.githubusercontent.com/mjm-12/transistor-hfe-measurement-circuit/'+commit+'/'+n))
assert sum(x['bytes'] for x in rows)==3081198 and len(rows)==3
cache={'README.md':'010-hfe-README.md','LICENSE':'011-hfe-LICENSE','transistor-hfe-measurement-circuit.kicad_pro':'012-hfe-transistor-hfe-measurement-circuit.kicad_pro'}
cachepins={name:p.sha(T/n) for name,n in cache.items()}
for name,n in cache.items():
 a=next(x for x in tree['tree'] if x['path']==name);raw=(T/n).read_bytes();assert len(raw)==a['size'] and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==a['sha']
 with (O/'source'/name).open('xb') as stream:stream.write(raw)
plan=dict(schema=1,repository='mjm-12/transistor-hfe-measurement-circuit',commit=commit,tree_sha256=TPIN,rows=rows,cached_originals_sha256=cachepins,max_new_requests=3,max_network_bytes=4*1024**2,whole_wall_full_cpu_seconds=120,source_scripts_or_models_executed=False,native_execution=False,scope='Only previously uninspected PCB/mainSCH/siblingSCH; previous004 dispositions and costs stay unchanged. Explicit hardware CERN-OHL-P-2.0 grant/fullbody retained; optional3Dmodel not acquired. Local raw source only, no redistribution, eligibility, pedigree or quality claim.')
p.save_json(O/'protocol.json',plan);planpin=p.sha(O/'protocol.json');record=dict(plan,accepted=False,passed=False,status='failed',requests=[])
def remaining():
 x=min(118-(time.monotonic()-START),118-(cpu()-CPU0))
 if x<=0:raise TimeoutError('finite HFE acquisition allowance exceeded')
 return x
try:
 for i,row in enumerate(rows):
  request={};record['requests'].append(request);raw=shared.fetch_one(row,request,O/'raw'/f'{i:02d}.bin',plan['max_network_bytes']-sum(x.get('received_bytes',0) for x in record['requests'][:-1]),remaining)
  assert len(raw)==row['bytes'] and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha1']
  request.update(git_blob_verified=True,source_path=row['source_path'])
  with (O/'source'/row['source_path']).open('xb') as stream:stream.write(raw)
 record.update(passed=True,status='completed',source_files_sha256=p.tree_hash(O/'source'))
except BaseException as ex:record['error']=type(ex).__name__+': '+str(ex)
material=p.tree_hash(O/'source')
def stable():
 h.owned_destination(owner)
 assert p.sha(T/'009-hfe-tree.json')==TPIN and p.sha(O/'protocol.json')==planpin and p.tree_hash(O/'source')==material
 assert all(p.sha(T/n)==cachepins[name] for name,n in cache.items())
def account():
 record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2,network_received_bytes=sum(x.get('received_bytes',0) for x in record['requests']))
 if remaining()<=0:record.update(passed=False,status='budget_exceeded')
f.publish(O,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
saved=f.read_json(O/'result.json');print(json.dumps({k:saved.get(k) for k in ['passed','status','network_received_bytes','wall_seconds','full_cpu_seconds','error','source_files_sha256']}));raise SystemExit(0 if saved['passed'] and saved['status']=='completed' else 2)
