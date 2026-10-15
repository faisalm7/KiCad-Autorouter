"""Freeze only two genuinely unattempted baseline settings; no Native launch."""
from pathlib import Path
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from experiments.universal_shift_recovery_v1 import b2
R=ROOT;target=b2.PROTOCOL;assert not target.exists()
prior='.runs/universal-own-C-ground-delete450-001/execution.json';old=f.read_json(R/prior);assert old['passed'] is True and old['source_current'] is True
cproto=f.read_json(R/'experiments/universal_shift_recovery_v1/input-pins.json');tools=p.tool_manifest()
assert {k:v for k,v in old['tools'].items() if k!='git_head'}=={k:v for k,v in tools.items() if k!='git_head'}
files=set((R/'autorouter').glob('*.py'))|set((R/'experiments').glob('**/*.py'))|set((R/'scripts').glob('*.py'))
for folder in ((R/prior).parent,R/'.runs/universal-shift-interface-original-native-001',Path(cproto['source']).parent):
 for file in folder.rglob('*'):
  assert not file.is_symlink(),file
  if file.is_file():files.add(file)
for name in (prior,'.runs/universal-shift-interface-native-paired300-readback-execution-001/execution.json','.runs/universal-shift-interface-native-paired300-readback-001/result.json','.runs/universal-shift-interface-native-paired300-002-protocol.json','.runs/run-universal-B2-missing450-001.py',str(Path(__file__).relative_to(R))):files.add(R/name)
pins={str(x.relative_to(R)):p.sha(x) for x in sorted(files)}
for name in ('experiments/universal_shift_recovery_v1/b2.py','experiments/native_paired_v1/observations.py'):
 raw=subprocess.check_output(['git','show',tools['git_head']+':'+name]);assert __import__('hashlib').sha256(raw).hexdigest()==pins[name]
spec=dict(schema=1,status='frozen',kind='universal-missing-B2-two-settings-v1',source=cproto['source'],source_hashes=cproto['source_hashes'],tools=tools,prior_execution=prior,prior_rows=old['final_charged_results'],original_receipt=cproto['original_receipt'],output=str(R/'.runs/universal-B2-missing450-001/work'),pins=pins,variants=['via_low','via_high'],assigned_seconds=90,selection='Existing portfolio rank: vias then length then declared variant order. Both observations retained.',budget=dict(actor_wall_and_full_cpu_seconds=220,whole_wall_and_full_cpu_seconds=240,cumulative_each_arm_wall_and_full_cpu_seconds=450),scope='Only missing B2low/high; original300/Cwholedelete failures unchanged. No Cwarm reuse or repeated oldNative/engine/whole readers.')
p.save_json(target,spec);print(json.dumps(dict(frozen=True,protocol_sha256=p.sha(target),pin_count=len(pins),tools_head=tools['git_head'])))
