from pathlib import Path
import ast,hashlib,json,datetime,copy,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx,pipeline as p
old=ROOT/'.runs/run-thermal-native-identity-component-001.py';out=ROOT/'.runs/run-thermal-native-identity-component-invalid-002.py'
raw=old.read_text();assert raw.count('sx.atom(')==4
# S-expression atoms are strings in the existing shared parser. No router code changes.
replacements={"sx.atom(n[1])":"n[1]","sx.atom(r[0])":"r[0]","sx.atom(sx.one(r,'net')[1])":"sx.one(r,'net')[1]","sx.atom(sx.one(track,'net')[1])":"sx.one(track,'net')[1]"}
# Replace only the four nonexistent wrapper calls in the copied harness.
for a,b in replacements.items():raw=raw.replace(a,b)
assert 'sx.atom(' not in raw
raw=raw.replace("choices=('legacy0','native7','invalid7','cancel7')","choices=('invalid7',)")
ast.parse(raw)
with out.open('x') as f:f.write(raw)
base=ROOT/'.runs/thermal-native-identity-controls-invalid-002';base.mkdir()
plan=json.loads((ROOT/'.runs/thermal-native-identity-controls-001/protocol.json').read_text());case=copy.deepcopy(plan['cases']['invalid7']);case['output']=str(ROOT/'.runs/runtime-directory-027/runtime/.runs/thermal-identity-invalid7-002')
# Exercise exactly the revised finite mutation code in memory before Native; no file or source mutation.
source=Path(plan['source']);original=p.preflight(source);tree=sx.read(case['input_candidate']);native_map=Path(case['input_native_map']);rows=json.loads(native_map.read_text())['nets'];classes={r['name']:r['class'] for r in rows if r['copper_pad_count']>0};protected=[x for x in p.routes(original) if p.locked(x)];names={n[1]:sx.unquote(n[2]) for n in sx.children(original,'net')};ids={name:i for i,name in names.items()}
track=next(r for r in p.routes(tree) if r[0]=='segment' and r not in protected and names.get(sx.one(r,'net')[1]) in classes);old_id=sx.one(track,'net')[1];old_name=names[old_id];new_name=next(n for n in sorted(classes) if n!=old_name and classes[n]==classes[old_name] and n in ids);before=copy.deepcopy(tree);sx.one(track,'net')[1]=ids[new_name];assert p.immutable(tree)==p.immutable(before) and sum(a!=b for a,b in zip(p.routes(tree),p.routes(before)))==1;assert all(x in p.routes(tree) for x in protected);assert sx.parse(sx.dump(tree))==tree
plan.update(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='bounded-invalid-native-thermal-identity-component-corrected-harness',controller_sha256=p.sha(out),cases={'invalid7':case},planned_order=['invalid7'],prior_protocol_sha256=p.sha(ROOT/'.runs/thermal-native-identity-controls-001/protocol.json'),prior_invalid_result_sha256=p.sha(ROOT/'.runs/runtime-directory-027/runtime/.runs/thermal-identity-invalid7-001/component-result.json'),revision_reason='001invalid used nonexistent sx.atom before any Native; atoms alreadystrings. Preserve failedcase and charge cost; correct harnessonly, no product/rule/algorithmchange or positivecase rerun.',mutation_precheck={'in_memory_only':True,'old_net':old_name,'new_net':new_name,'same_native_class':classes[old_name],'one_unprotected_route_net_only':True,'all_immutable_geometry_unchanged':True,'roundtrip':True},cancel_gate='No cancellation case in002. Existing001cancel remains separate, one actualattempt only after controls.')
p.save_json(base/'protocol.json',plan)
outer=(ROOT/'.runs/enclose-thermal-native-identity-001.py').read_text();outer=outer.replace("assert label in ('legacy0','native7','invalid7')","assert label=='invalid7'");outer=outer.replace("ROOT/'.runs/thermal-native-identity-controls-001'","ROOT/'.runs/thermal-native-identity-controls-invalid-002'");outer=outer.replace("ROOT/'.runs/run-thermal-native-identity-component-001.py'","ROOT/'.runs/run-thermal-native-identity-component-invalid-002.py'");ast.parse(outer)
with (ROOT/'.runs/enclose-thermal-native-identity-invalid-002.py').open('x') as f:f.write(outer)
print(json.dumps({'protocol_sha256':p.sha(base/'protocol.json'),'precheck':plan['mutation_precheck']}))
