"""Stored-metadata helper replay only; old90 controls do not qualify new420 contracts."""
from pathlib import Path
from collections import Counter
from types import SimpleNamespace
import ast,copy,hashlib,json,math,resource,re,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import provenance as pv,placement_clearance as io
BASE=Path(__file__).resolve().parent;START=time.monotonic();CPU=time.process_time()
SOURCE=ROOT/'scripts/report_current_comparison.py';PIN='0e4cbed10b1ee09f3613dd2aadcd3d0f94c632bc700691334a0dcd7004bfcfba'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(SOURCE)==PIN
ns=dict(Path=Path,Counter=Counter,hashlib=hashlib,json=json,math=math,re=re,pv=pv,io=io,
        MAX_JSON=4*1024**2,KEYS=('opens','blocking','warnings','exclusions'))
# Exact AST-defined canonical utility and reporter functions; no report main,
# comparison freezer/method invocation, Native or central acceptance reader.
floor=ROOT/'autorouter/floor_route.py';canon=[n for n in ast.parse(floor.read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='canonical']
assert len(canon)==1;fns={'json':json};exec(compile(ast.Module(body=canon,type_ignores=[]),str(floor),'exec'),fns);ns['f']=SimpleNamespace(canonical=fns['canonical'])
names={'require','digest','read','counts','field_fact','finding_types','ignored_check_facts','own_final','improve_auxiliary'}
funcs=[n for n in ast.parse(SOURCE.read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name in names]
assert {n.name for n in funcs}==names;exec(compile(ast.Module(body=funcs,type_ignores=[]),str(SOURCE),'exec'),ns)
read=ns['read'];own_final=ns['own_final'];auxiliary=ns['improve_auxiliary']
proto=ROOT/'.runs/runtime050-native-qualification-001/improve-fractional/protocol.json';plan=read(proto)
child=read(Path(plan['output'])/'result.json');workspace=Path(child['workspace']);folder=workspace/'route'
parent_path=folder/'result.json';parent=read(parent_path)
assert parent['budget_seconds']==parent['cpu_budget_seconds']==90 and parent['accepted']is True
assert child['workflow_delivered']is True and plan['method']=='improve'
assert len(parent['trials'])==1 and parent['trials'][0]['id']=='trial-0000'
source_before=io.inventory(Path(plan['source']).parent);before=io.inventory(workspace)
inputs={'protocol':sha(proto),'child':sha(Path(plan['output'])/'result.json')}
cases=[('parent',parent_path,folder,False,None),('incumbent',folder/'incumbent/result.json',folder/'incumbent',False,None),
 ('trial-0000',folder/'trials/trial-0000/result.json',folder/'trials/trial-0000',False,parent),
 ('export',workspace/'export/export.json',workspace/'export/validation',True,None)]
results=[];faults=[];unexpected=[]
for label,path,proof_folder,export,trial_parent in cases:
 data=read(path);inputs[label]=sha(path)
 try:
  proof=own_final(path,export=export,plan=plan,allowed=[workspace],accepted=True,public_sanitize=True,trial_parent=trial_parent)
  extra=auxiliary(proof_folder,data,plan)
  assert proof['Native_counts']==[0,0,6,0] and extra['field_qualification']['qualified']is True
  results.append(dict(role=label,passed=True,receipt_sha256=sha(path),own_final=proof,auxiliary=extra))
 except Exception as exc:
  results.append(dict(role=label,passed=False,error=type(exc).__name__+': '+str(exc)));unexpected.append(label)
trial_path=folder/'trials/trial-0000/result.json';trial=read(trial_path);trial_folder=trial_path.parent
original_read=ns['read']
def run_fault(name,call,*,overrides=None,missing=(),expected_refusal=False,check=None):
 def patched(path):
  path=Path(path)
  if path in missing:raise FileNotFoundError('isolated in-memory missing proof: '+path.name)
  return copy.deepcopy(overrides[path]) if overrides and path in overrides else original_read(path)
 ns['read']=patched
 try:
  value=call()
  if expected_refusal:raise AssertionError('expected refusal but helper returned')
  if check:assert check(value)
  row=dict(name=name,passed=True,outcome='returned expected metadata facts')
 except (ValueError,FileNotFoundError)as exc:
  row=dict(name=name,passed=expected_refusal,outcome='refused',error=type(exc).__name__+': '+str(exc))
 except Exception as exc:row=dict(name=name,passed=False,error=type(exc).__name__+': '+str(exc))
 finally:ns['read']=original_read
 faults.append(row)
 if not row['passed']:unexpected.append(name)
def own_trial():return own_final(trial_path,export=False,plan=plan,allowed=[workspace],accepted=False,public_sanitize=True,trial_parent=parent)
quality=copy.deepcopy(trial);quality.update(status='quality_rejected',accepted=False)
run_fault('Native-valid quality_rejected is unselected, not routing-negative',own_trial,overrides={trial_path:quality},check=lambda v:v['Native_counts']==[0,0,6,0])
bad=copy.deepcopy(quality);bad['status']='drc_rejected'
run_fault('drc_rejected requires actual nonzero failing routing counts',own_trial,overrides={trial_path:bad},expected_refusal=True)
bad=copy.deepcopy(trial);bad['native_report_sha256']='0'*64
run_fault('changed declared Native report hash refuses',lambda:own_final(trial_path,export=False,plan=plan,allowed=[workspace],accepted=True,public_sanitize=True,trial_parent=parent),overrides={trial_path:bad},expected_refusal=True)
proof_path=trial_folder/'final-drc-fields-proof.json';proof=read(proof_path);false=copy.deepcopy(proof);false['qualification']['qualified']=False
bad=copy.deepcopy(trial);bad['native']['field_parity']=false
run_fault('field record/proof mismatch refuses',lambda:auxiliary(trial_folder,bad,plan),expected_refusal=True)
run_fault('matching qualified-False is explicitly reported False, never upgraded',lambda:auxiliary(trial_folder,bad,plan),overrides={proof_path:false},check=lambda v:v['field_qualification']['qualified']is False)
run_fault('missing own field proof refuses',lambda:auxiliary(trial_folder,trial,plan),missing=(proof_path,),expected_refusal=True)
audit_path=trial_folder/'final-netclass-audit.json';bad_audit=read(audit_path);bad_audit['native_map_file_sha256']='0'*64
run_fault('changed own Default map hash refuses',lambda:auxiliary(trial_folder,trial,plan),overrides={audit_path:bad_audit},expected_refusal=True)
assert io.inventory(workspace)==before and io.inventory(Path(plan['source']).parent)==source_before
assert sha(SOURCE)==PIN and 'autorouter.native'not in sys.modules
source_paths=[SOURCE,ROOT/'autorouter/provenance.py',ROOT/'autorouter/placement_clearance.py',floor]
report=dict(schema=1,kind='runtime050-stored-Improve-report-helper-schema-review-v1',accepted=False,Native_executed=False,
 central_readers_executed=False,actual_GUI=False,human_review=False,source_sha256_before=PIN,source_sha256_after=sha(SOURCE),
 utility_source_sha256={str(p.relative_to(ROOT)):sha(p)for p in source_paths},inputs_sha256=inputs,
 source_and_workspace_unchanged=True,workspace_inventory_sha256=hashlib.sha256(fns['canonical'](before).encode()).hexdigest(),
 source_hashes=source_before,actual_completed_roles=results,in_memory_fault_controls=faults,unexpected=unexpected,
 scope='Only actual owned050 fractional90 own_final/improve_auxiliary schema; no full improve_facts, no420 contract qualification or new Native/central acceptance proof. In-memory fault substitutions do not modify or replace original evidence.',
 auxiliary_semantics='qualified=False remains an explicit reported fact; auxiliary/own-final metadata helpers are not standalone admission readers. Comparison classification and central production qualification remain separate.',
 source_only_AI_review=True,generator_independent=False,all_helpers_passed=not unexpected,
 sampled_wall_seconds=time.monotonic()-START,sampled_CPU_seconds=time.process_time()-CPU,
 complete_external_time_log=str(BASE/'time.log'))
with(BASE/'result.json').open('x')as stream:json.dump(report,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps(dict(actual_roles=len(results),fault_controls=len(faults),passed=not unexpected,unexpected=unexpected,result_sha256=sha(BASE/'result.json'))))
raise SystemExit(bool(unexpected))
