"""Freeze one current C200 continuation; preserve failed750 state and all costs."""
from pathlib import Path
import sys,json,subprocess,hashlib
R=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
T=R/'.runs/universal-preparation950-001-protocol.json';assert not T.exists()
prior='.runs/universal-native-reserve750-001/execution.json';old=f.read_json(R/prior);base=f.read_json(R/'.runs/universal-native-reserve750-001-protocol.json');tools=p.tool_manifest()
state={k:old[k] for k in ('passed','source_current','reason')}
assert state==dict(passed=False,source_current=False,reason='Rejected: normal DRC retained worker population differs from steps')
assert old['tools']==base['tools'] and old['protocol_sha256']==p.sha(R/'.runs/universal-native-reserve750-001-protocol.json')
before=old['tools']
def normalize(t):
 t=json.loads(json.dumps(t));t.pop('git_head')
 for name in ('autorouter/strategy.py','autorouter/pipeline.py'):t['implementation_sha256'].pop(name)
 return t
assert normalize(before)==normalize(tools)
for name in ('autorouter/strategy.py','autorouter/pipeline.py'):assert before['implementation_sha256'][name]!=tools['implementation_sha256'][name]
bindings={'autorouter/strategy.py':'evidence/universal750-prelaunch-failure-001/producer-strategy.py','autorouter/pipeline.py':'evidence/universal750-prelaunch-failure-001/producer-pipeline.py','experiments/universal_shift_recovery_v1/pruning_readback.py':'evidence/universal-preparation950-source-001/producer-pruning-readback.py'}
retained={};captures={}
for expected in (base['pins'],base['retained_original_pins']):
 for name,pin in expected.items():
  path=R/name
  if p.sha(path)!=pin:
   assert name in bindings,('retained evidence changed',name)
   capture=bindings[name];assert p.sha(R/capture)==pin,('old producer capture changed',name)
   captures[name]=dict(expected_sha256=pin,captured_old=capture,current_sha256=p.sha(path));name=capture
  assert name not in retained or retained[name]==pin,('conflicting retained digest',name)
  retained[name]=pin
# One accepted standalone B2 survived the failed enclosing observer. No solver rerun.
b2path='.runs/universal-native-reserve750-001/B2_long_low/result.json';b2=f.read_json(R/b2path)
qualified=next(x for x in old['observations'] if x['id']=='B2_long_low')
assert qualified['checks']['passed'] is True and qualified['checks']['candidate_valid'] is True
assert qualified['result']==str(R/b2path) and qualified['result_sha256']==p.sha(R/b2path)
assert b2['accepted'] is True and b2['tools']==before and b2['budget_seconds']==b2['cpu_budget_seconds']==200
assert (b2['scope'],b2['adapter'],b2['engine_profile'],b2['scoring_variant'])==('whole_board_unlocked_routing','both','tuned','via_low')
files=set((R/'autorouter').glob('*.py'))|set((R/'experiments').glob('**/*.py'))|set((R/'scripts').glob('*.py'));files.update(R/name for name in retained)
for folder in ((R/prior).parent,R/'.runs/universal-shift-interface-original-native-001',Path(base['source']).parent):
 for file in folder.rglob('*'):
  assert not file.is_symlink(),file
  if file.is_file():files.add(file)
for name in (prior,'.runs/universal-native-reserve750-001-protocol.json','.runs/run-universal-preparation950-001.py',str(Path(__file__).relative_to(R)),bindings['experiments/universal_shift_recovery_v1/pruning_readback.py']):files.add(R/name)
pins={str(x.relative_to(R)):p.sha(x) for x in sorted(files)}
for name in ('experiments/universal_shift_recovery_v1/pruning_readback.py','experiments/universal_shift_recovery_v1/cli_entry.py'):
 assert hashlib.sha256(subprocess.check_output(['git','show',tools['git_head']+':'+name])).hexdigest()==pins[name]
spec=dict(schema=1,status='frozen',kind='universal-preparation950-v1',source=base['source'],source_hashes=base['source_hashes'],tools=tools,prior_execution=prior,prior_execution_sha256=p.sha(R/prior),prior_state=state,prior_rows=old['final_charged_results'],original_receipt=base['original_receipt'],pins=pins,retained_original_pins=retained,retained_producer_captures=captures,retained_b2=dict(result=b2path,result_sha256=p.sha(R/b2path),tools=b2['tools'],candidate_sha256=b2['candidate_sha256'],native_report_sha256=b2['native_report_sha256']),method_order=['C_feedback'],individual_wall_full_cpu_seconds=200,native_final_reserve_seconds=25,whole_wall_full_cpu_seconds=250,cumulative_each_arm_wall_full_cpu_seconds=950,publication_allowance_seconds=4,startup_allowance_seconds=1,retained_runtime_deltas={name:dict(old_sha256=before['implementation_sha256'][name],new_sha256=tools['implementation_sha256'][name],captured_old=bindings[name]) for name in ('autorouter/strategy.py','autorouter/pipeline.py')},scope='Exposed development. Old750 remains rejected. All old costs retained; one fresh own-incumbent C200, no B2 Native repeat/warm reuse. Retained standalone B2 is selected only after measured p.check_result. New shared/check/publication overhead is charged to every row. B0/B1 old false rows stay false. Original Native/rules/classes/PRL/warnings/ignored/final/cost checks unchanged. No broad/physical/human/release claim.')
p.save_json(T,spec);print(json.dumps(dict(frozen=True,protocol_sha256=p.sha(T),pins=len(pins),head=tools['git_head'],prior_state=state)))
