"""Pure actual-evidence reconstruction and exact-only guard checks; no native."""
from pathlib import Path
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx
OUT=Path(__file__).resolve().parent
BASE=ROOT/'evidence/preferences-native-qualification-001/preferences-native-partial-001'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
files={str(x.relative_to(BASE)):sha(x) for x in BASE.rglob('*') if x.is_file()}
code={n:sha(ROOT/n) for n in ('autorouter/pipeline.py','autorouter/sexpr.py','tests/test_protected_import.py')}
original=sx.read(BASE/'snapshot/smoke.kicad_pcb');imported=sx.read(BASE/'imported.kicad_pcb')
protected=copy.deepcopy(p.routes(original));before=copy.deepcopy((original,imported))
result=p.transplant_routes(original,imported,protected=protected)
signature=lambda route:sx.dump([n for n in route if not isinstance(n,list) or not n or n[0]!='uuid'])
converted=[p.convert_route_nets(n,imported,original) for n in p.routes(imported)]
checks=[]
def check(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
check('exactly_two_original_protected_segments',len(protected)==2 and all(n[0]=='segment' for n in protected))
check('all_original_protected_nodes_exact',all(n in p.routes(result) for n in protected))
check('all_imported_nonuuid_AST_fields_unchanged',[signature(n) for n in p.routes(result)]==[signature(n) for n in converted])
check('immutable_geometry_unchanged',p.immutable(result)==p.immutable(original))
check('arguments_unchanged',(original,imported)==before)
rows=[]
for n in protected:
 matches=[r for r in converted if signature(r)==signature(n)]
 check('unique_match_'+sx.one(n,'uuid')[1],len(matches)==1)
 rows.append({'original_uuid':sx.unquote(sx.one(n,'uuid')[1]),'imported_uuid':sx.unquote(sx.one(matches[0],'uuid')[1]),'signature_sha256':hashlib.sha256(signature(n).encode()).hexdigest()})
for kind in ('unknown_field','route_kind','start_offset','endpoint_reversed','numeric_spelling','lock_added'):
 trial=copy.deepcopy(imported)
 match=next(n for n in p.routes(trial) if signature(p.convert_route_nets(n,trial,original))==signature(protected[0]))
 if kind=='unknown_field':match.append(['future_route_constraint','required'])
 elif kind=='route_kind':match[0]='arc'
 elif kind=='start_offset':sx.one(match,'start')[1]=str(float(sx.one(match,'start')[1])+1)
 elif kind=='endpoint_reversed':
  a=sx.one(match,'start');b=sx.one(match,'end');a[1:],b[1:]=b[1:],a[1:]
 elif kind=='numeric_spelling':sx.one(match,'width')[1]+='0'
 elif kind=='lock_added':match.append(['locked','yes'])
 try:p.transplant_routes(original,trial,protected=protected)
 except p.Rejected:check('reject_'+kind,True)
 else:check('reject_'+kind,False)
check('public_run_all_bytes_unchanged',files=={str(x.relative_to(BASE)):sha(x) for x in BASE.rglob('*') if x.is_file()})
check('reviewed_source_unchanged',code=={n:sha(ROOT/n) for n in code})
record={'scope':'Offline reconstruction from actual failed native import plus pure mutation controls; no new routing or native success.', 'source_sha256':code,'actual_failed_result_sha256':sha(BASE/'result.json'),'actual_imported_sha256':sha(BASE/'imported.kicad_pcb'),'actual_original_sha256':sha(BASE/'snapshot/smoke.kicad_pcb'),'actual_failure':json.loads((BASE/'result.json').read_text())['reason'],'original_protected_count':len(protected),'imported_route_count':len(converted),'restored_identities':rows,'checks':checks,'all_passed':all(x['passed'] for x in checks)}
(OUT/'audit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'all_passed':record['all_passed'],'source':code}))
