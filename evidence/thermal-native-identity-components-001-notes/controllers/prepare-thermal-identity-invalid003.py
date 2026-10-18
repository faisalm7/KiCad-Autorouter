from pathlib import Path
import ast,json,datetime,copy,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
old=ROOT/'.runs/run-thermal-native-identity-component-invalid-002.py';raw=old.read_text();start=raw.index('  track=next(');end=raw.index('\n stable();print(',start)
new="""  candidates=[]
  zone_ids={sx.one(z,'net')[1] for z in sx.children(tree,'zone') if sx.one(z,'net') is not None}
  protected_ids={sx.one(r,'net')[1] for r in protected}
  for name in sorted(classes):
   net_id=ids.get(name);rows_for_net=[r for r in rows if r['name']==name]
   copper=[r for r in p.routes(tree) if sx.one(r,'net')[1]==net_id]
   if net_id is not None and net_id not in zone_ids and net_id not in protected_ids and len(rows_for_net)==1 and rows_for_net[0]['copper_pad_count']==2 and copper:candidates.append((name,net_id,copper))
  assert candidates,'no deterministic nonplane2padunprotectednet fixture'
  name,net_id,removed=candidates[0];before=copy.deepcopy(tree);tree[:]=[x for x in tree if x not in removed]
  assert p.immutable(tree)==p.immutable(before) and all(x in p.routes(tree) for x in protected) and p.routes(tree)==[r for r in p.routes(before) if r not in removed]
  candidate.write_text(sx.dump(tree)+'\\n')
  report['deliberate_candidate_fault']=dict(kind='disconnect a deterministic2pad nonplane source net by removing all its unprotected candidate routing',net=name,net_code=net_id,removed_count=len(removed),original_source_changed=False,original_geometry_unchanged=True,protected_unchanged=True)"""
raw=raw[:start]+new+raw[end:];out=ROOT/'.runs/run-thermal-native-identity-component-invalid-003.py';ast.parse(raw)
with out.open('x') as f:f.write(raw)
base=ROOT/'.runs/thermal-native-identity-controls-invalid-003';base.mkdir();prior=ROOT/'.runs/thermal-native-identity-controls-invalid-002/protocol.json';plan=json.loads(prior.read_text());case=plan['cases']['invalid7'];case['output']=str(ROOT/'.runs/runtime-directory-027/runtime/.runs/thermal-identity-invalid7-003')
# Run the exact fixture block in memory first; it only writes to a non-filesystem sink.
class Sink:
 def write_text(self,s):self.value=s
source=Path(plan['source']);original=p.preflight(source);tree=sx.read(case['input_candidate']);rows=json.loads(Path(case['input_native_map']).read_text())['nets'];classes={r['name']:r['class'] for r in rows if r['copper_pad_count']>0};names={n[1]:sx.unquote(n[2]) for n in sx.children(original,'net')};ids={name:i for i,name in names.items()};protected=[r for r in p.routes(original) if p.locked(r)];candidate=Sink();report={}
exec(compile('\n'.join(line[2:] for line in new.splitlines()),'<exact-inmemory-negative-fixture>','exec'))
assert sx.parse(candidate.value)==tree
plan.update(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),controller_sha256=p.sha(out),prior_protocol_sha256=p.sha(prior),prior_invalid_result_sha256=p.sha(ROOT/'.runs/runtime-directory-027/runtime/.runs/thermal-identity-invalid7-002/component-result.json'),revision_reason='002actualNative refills reassigned the wrong-net segment back and existing route-identity invariant refused before full validation. Preserve this legitimate failclosed behavior as attempted/unqualified for plannedeligibility. Revise only negative fixture to remove deterministic2pad nonplane unprotected routing, expecting actualNative opens and no thermal eligibility; no product/guard/algorithmchange or positive rerun.',mutation_precheck=dict(report['deliberate_candidate_fault'],in_memory_only=True,roundtrip=True),controls='Actual candidate incomplete connection; source remains immutable and not labelledinvalidsource. Freshoriginal/fullSCHNative must observe opens>0 orblocking>1; solethermal mustbeNone and geometry/trialsabsent.120wall/fullCPU, one actualattempt.',nonadmission=plan['nonadmission'])
p.save_json(base/'protocol.json',plan)
outer=(ROOT/'.runs/enclose-thermal-native-identity-invalid-002.py').read_text().replace('controls-invalid-002','controls-invalid-003').replace('component-invalid-002.py','component-invalid-003.py');ast.parse(outer)
with (ROOT/'.runs/enclose-thermal-native-identity-invalid-003.py').open('x') as f:f.write(outer)
print(json.dumps({'protocol_sha256':p.sha(base/'protocol.json'),'precheck':plan['mutation_precheck']}))
