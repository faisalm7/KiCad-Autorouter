"""Read retained Native stages with existing readers; no Native execution."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];runtime=Path(sys.argv[1]);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,thermal
protocol=Path(sys.argv[2]);label=sys.argv[3];plan=f.read_json(protocol);case=plan['cases'][label];out=Path(case['output']);r=f.read_json(out/'component-result.json');original=sx.read(plan['source']);protected=[x for x in p.routes(original) if p.locked(x)]
assert r['tools']==p.tool_manifest() and r['protocol_sha256']==p.sha(protocol) and r['source_originals_unchanged'] and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']==p.tree_hash(out/'snapshot')
assert p.sha(Path(case['input_candidate']))==case['input_candidate_sha256'] and r['accepted'] is False and r['routing_accepted'] is False and r['production_admitted'] is False and all(s['cleanup_complete'] for s in r['steps'])
records=[]
def validate(directory,data,final=True):
 candidate=directory/'candidate'/Path(plan['source']).name;pre=directory/'pre-refill.kicad_pcb';refill=directory/'refill'/candidate.name
 expected={**plan['source_hashes'],candidate.name:p.sha(pre)}
 steps=[s for s in data['steps'] if s['cwd']==str(directory)]
 stage=next(s for s in steps if s['name']=='refill-drc');sandboxed=stage['argv'][0]=='/usr/bin/sandbox-exec'
 f.check_drc_stage(directory,data,'refill-drc',refill,refill,True,expected,sandboxed=sandboxed);records.append(str(directory/'refill-drc.json'))
 if final:
  expected[candidate.name]=p.sha(candidate);native=f.check_drc_stage(directory,data,'final-drc',candidate,directory/'final-drc-input'/candidate.name,False,expected,schematic_parity=True,sandboxed=sandboxed)
  assert p.immutable(sx.read(candidate))==p.immutable(original) and all(x in p.routes(sx.read(candidate)) for x in protected)
  p.verify_candidate_files(candidate,plan['source_hashes'],p.sha(candidate));records.append(str(directory/'final-drc.json'));return native
if label=='cancel7':
 validate(out,r,False);last=r['steps'][-1];assert r['status']=='cancelled' and not r['component_passed'] and last['name']=='final-drc' and last['status']=='cancelled' and last['cancel_signal']=='SIGINT' and last['cleanup_complete'] and 'repair' not in r and not (out/'recovery').exists()
else:
 native=validate(out,r);assert native==r['prevalidation_native']
 if 'invalid' in protocol.parent.name and protocol.parent.name.endswith('002'):
  raise AssertionError('002 intentionally has no final validation; read early refill only separately')
 if label=='invalid7':
  q=r['repair'];assert r['component_passed'] and native['opens']==1 and native['blocking']==1 and thermal.sole_thermal(native) is None and q['validation_passed'] is False and q['geometry_receipt'] is None and not q['trials']
 else:
  q=r['repair'];assert r['component_passed'] and q['validation_passed'] and thermal.sole_thermal(native) is not None and len(q['trials'])==1
  g=f.read_json(out/'recovery/geometry.json');thermal._check_geometry_identity(g)
  for trial in q['trials']:
   d=Path(trial['candidate']).parent.parent;data={**r,'steps':trial['steps']};n=validate(d,data);assert n==trial['native'] and p.native_accepted(n) and [n[k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,22,0] and p.sha(Path(trial['candidate']))==trial['candidate_sha256']==q['candidate_sha256']
result=dict(runtime=str(runtime),case=label,protocol_sha256=p.sha(protocol),source_originals_unchanged=True,readback_passed=True,Native_executed=False,overall_accepted=False,production_admitted=False,checked_DRC_records=records,actual_status=r['status'],final_native_counts=([r['prevalidation_native'][k] for k in ('opens','blocking','warnings','exclusions')] if label=='invalid7' else [0,0,22,0] if label!='cancel7' else None),cancel_phase='final-drc' if label=='cancel7' else None)
print(json.dumps(result))
