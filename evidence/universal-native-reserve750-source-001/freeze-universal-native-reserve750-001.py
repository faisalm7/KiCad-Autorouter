"""Freeze a new current-source comparison, retaining all failed450 costs."""
from pathlib import Path
import sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
T=R/'.runs/universal-native-reserve750-001-protocol.json';assert not T.exists()
prior='.runs/universal-own-low-pruning450-001/execution.json';old=f.read_json(R/prior);base=f.read_json(R/'.runs/universal-own-low-pruning450-001-protocol.json');tools=p.tool_manifest()
assert old['passed'] is True and old['source_current'] is True and old['candidate_valid'] is False
before=old['tools'];assert before['implementation_sha256']['autorouter/strategy.py']!=tools['implementation_sha256']['autorouter/strategy.py']
def normalize(t):
 t=json.loads(json.dumps(t));t.pop('git_head');t['implementation_sha256'].pop('autorouter/strategy.py');return t
assert normalize(before)==normalize(tools)
producer='evidence/universal-own-low-pruning450-failure-001/strategy.py';assert p.sha(R/producer)==before['implementation_sha256']['autorouter/strategy.py']
# Retained outcomes are evidence at their ORIGINAL digests, never freshly reanchored.
# Old producer code has explicit immutable captures for the two intended changes.
old_helper='evidence/universal-native-reserve750-source-001/producer-pruning-readback.py'
bindings={'autorouter/strategy.py':producer,'experiments/universal_shift_recovery_v1/pruning_readback.py':old_helper}
b2=f.read_json(R/'.runs/universal-B2-missing450-001-protocol.json')
cprobe=f.read_json(R/'experiments/universal_shift_recovery_v1/input-pins.json')
old300=f.read_json(R/'.runs/universal-shift-interface-native-paired300-002-protocol.json')
maps=[base['pins'],b2['pins'],cprobe['pins'],old300['freeze']['files_sha256'],old300['common_prerequisites']['pins'],old300['prior_matrix']['pins'],old300['complete_source_files_sha256'],old300['netclass_delta']['control']['pins']]
retained={};captures={}
for expected in maps:
 for name,pin in expected.items():
  path=R/name
  if p.sha(path)!=pin:
   assert name in bindings,('retained evidence changed',name)
   capture=bindings[name];assert p.sha(R/capture)==pin,('old producer capture changed',name)
   captures[name]=dict(expected_sha256=pin,captured_old=capture,current_sha256=p.sha(path));name=capture
  assert name not in retained or retained[name]==pin,('conflicting old digests',name)
  retained[name]=pin
files=set((R/'autorouter').glob('*.py'))|set((R/'experiments').glob('**/*.py'))|set((R/'scripts').glob('*.py'))
files.update(R/name for name in retained)
for folder in ((R/prior).parent,R/'.runs/universal-shift-interface-original-native-001',Path(base['source']).parent):
 for file in folder.rglob('*'):
  assert not file.is_symlink(),file
  if file.is_file():files.add(file)
for name in (producer,prior,'.runs/universal-own-low-pruning450-001-protocol.json','.runs/run-universal-native-reserve750-001.py',str(Path(__file__).relative_to(R))):files.add(R/name)
pins={str(x.relative_to(R)):p.sha(x) for x in sorted(files)}
for name in ('experiments/universal_shift_recovery_v1/pruning_readback.py','experiments/universal_shift_recovery_v1/cli_entry.py'):
 assert hashlib.sha256(subprocess.check_output(['git','show',tools['git_head']+':'+name])).hexdigest()==pins[name]
spec=dict(schema=1,status='frozen',kind='universal-native-reserve750-v1',source=base['source'],source_hashes=base['source_hashes'],tools=tools,prior_execution=prior,prior_rows=old['final_charged_results'],original_receipt=base['original_receipt'],pins=pins,retained_original_pins=retained,retained_producer_captures=captures,method_order=['B2_long_low','C_feedback'],individual_wall_full_cpu_seconds=200,native_final_reserve_seconds=25,whole_wall_full_cpu_seconds=510,cumulative_each_arm_wall_full_cpu_seconds=750,publication_allowance_seconds=4,startup_allowance_seconds=1,retained_runtime_delta=dict(path='autorouter/strategy.py',old_sha256=before['implementation_sha256']['autorouter/strategy.py'],new_sha256=tools['implementation_sha256']['autorouter/strategy.py'],captured_old=producer,all_other_core_native_tools_exact=True),scope='Exposed development. New source and same individual200caps; allfailed450 costs remain. Stronger B2low200 fromoriginal, ownfreshC200lowincumbent+feedback, noB2warm reuse. Every Nativefinal/source/rule/class/refill/warning/ignored/PRL/CPU retained; old450remainsrejected. PreviousvalidB2 retained in portfolio if newrunfails; both raw newoutcomesreported. No broad/physical/human/releaseclaim.')
p.save_json(T,spec);print(json.dumps(dict(frozen=True,protocol_sha256=p.sha(T),pins=len(pins),head=tools['git_head'],only_core_delta=spec['retained_runtime_delta'])))
