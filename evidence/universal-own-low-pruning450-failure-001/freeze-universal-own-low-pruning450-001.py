"""Prospectively freeze an existing product CLI run; no Native execution."""
from pathlib import Path
import sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
T=R/'.runs/universal-own-low-pruning450-001-protocol.json';assert not T.exists()
prior='.runs/universal-B2-missing450-001/execution.json';old=f.read_json(R/prior);assert old['passed'] is True and old['source_current'] is True
base=f.read_json(R/'.runs/universal-B2-missing450-001-protocol.json');tools=p.tool_manifest();assert {k:v for k,v in old['tools'].items() if k!='git_head'}=={k:v for k,v in tools.items() if k!='git_head'}
files=set((R/'autorouter').glob('*.py'))|set((R/'experiments').glob('**/*.py'))|set((R/'scripts').glob('*.py'))
for folder in ((R/prior).parent,R/'.runs/universal-shift-interface-original-native-001',Path(base['source']).parent):
 for file in folder.rglob('*'):
  assert not file.is_symlink(),file
  if file.is_file():files.add(file)
for name in (prior,'.runs/universal-B2-missing450-001-protocol.json','.runs/run-universal-own-low-pruning450-001.py',str(Path(__file__).relative_to(R))):files.add(R/name)
pins={str(x.relative_to(R)):p.sha(x) for x in sorted(files)}
for name in ('experiments/universal_shift_recovery_v1/pruning_readback.py','experiments/universal_shift_recovery_v1/cli_entry.py'):
 raw=subprocess.check_output(['git','show',tools['git_head']+':'+name]);assert hashlib.sha256(raw).hexdigest()==pins[name]
spec=dict(schema=1,status='frozen',kind='universal-own-low-pruning450-v1',source=base['source'],source_hashes=base['source_hashes'],tools=tools,prior_execution=prior,prior_rows=old['final_charged_results'],original_receipt=base['original_receipt'],output=str(R/'.runs/universal-own-low-pruning450-001/work'),pins=pins,product_cli=['improve',base['source'],'--seconds','200','--proposal-policy','feedback','--scoring-preference','via_low'],limits=dict(product_wall_full_cpu_seconds=200,enclosing_wall_full_cpu_seconds=250,cumulative_each_arm_wall_full_cpu_seconds=450,log_bytes=4*1024**2,output_bytes=512*1024**2,group_rss_bytes=2*1024**3),scope='Own fresh original-source low-scoring incumbent and unchanged product pruning. No B2candidate reuse, no oldNative/engine/whole reader repeat. Allpriorcosts/failures/all81warnings/fiveignored/fulloriginalrules remain. Exposeddevelopment; no broad scientific/physical release claim.')
assert next(r for r in spec['prior_rows'] if r['id']=='C_feedback')['charged_wall_seconds']+253<450
assert next(r for r in spec['prior_rows'] if r['id']=='C_feedback')['charged_cpu_seconds']+253<450
p.save_json(T,spec);print(json.dumps(dict(frozen=True,protocol_sha256=p.sha(T),pins=len(pins),head=tools['git_head'])))
