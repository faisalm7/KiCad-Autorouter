"""Freeze one already reviewed prospective diagnostic; never launches Native."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
R=ROOT;target=R/'experiments/universal_shift_recovery_v1/input-pins.json';assert not target.exists()
prior='.runs/universal-shift-interface-native-paired300-readback-execution-001/execution.json'
warm='.runs/universal-shift-interface-native-paired300-002/run/C_feedback/incumbent/result.json'
original='.runs/universal-shift-interface-original-native-001/result.json'
w=f.read_json(R/warm);previous=f.read_json(R/prior);assert previous['passed'] is True and previous['source_current'] is True
files=set((R/'autorouter').glob('*.py'))|set((R/'experiments').glob('**/*.py'))
for folder in ((R/warm).parent,(R/original).parent,Path(w['source']).parent):
 for file in folder.rglob('*'):
  assert not file.is_symlink(),file
  if file.is_file():files.add(file)
for name in (prior,warm,original,'.runs/universal-shift-interface-native-paired300-readback-001/result.json','.runs/universal-shift-interface-native-paired300-002-protocol.json','.runs/run-universal-own-C-ground-delete450-001.py',str(Path(__file__).relative_to(R)),'evidence/universal-own-C-ground-delete450-source-001/dry-proposal-result-001.json'):
 files.add(R/name)
pins={str(x.relative_to(R)):p.sha(x) for x in sorted(files)}
spec=dict(schema=1,status='frozen',kind='universal-own-C-whole-zone-deletion-v1',source=w['source'],source_hashes=w['source_hashes'],tools=p.tool_manifest(),prior_reader_execution=prior,prior_rows=previous['final_charged_results'],warm_receipt=warm,warm_sha256=w['candidate_sha256'],original_receipt=original,output=str(R/'.runs/universal-own-C-ground-delete450-001/work'),pins=pins,preflight_charge=dict(wall_seconds=4.514397666993318,full_cpu_seconds=2.774211,publication_allowance_seconds=2),budget=dict(actor_wall_and_full_cpu_seconds=45,whole_wall_and_full_cpu_seconds=60,cumulative_each_arm_wall_and_full_cpu_seconds=450),scope='Fresh own-C whole-zone deletion only; old300 all rejected unchanged. Root diagnostic acceptedFalse/productionFalse. RemainingB2low/high required before any comparison. All source rules/warnings/protected routes exact.')
assert all(x['accepted'] is False for x in spec['prior_rows']);assert w['candidate_sha256']=='b276450285ffa7f3daa42001ec622ca775a2d34e1590af473e5ace16a1096845'
p.save_json(target,spec)
print(json.dumps(dict(frozen=True,protocol_sha256=p.sha(target),pin_count=len(pins),tools_head=spec['tools']['git_head'],prior_rows=[{k:r[k] for k in ('id','accepted','charged_wall_seconds','charged_cpu_seconds')} for r in spec['prior_rows']]),indent=2))
