"""Preserve failed relative wrapper invocation; fresh identical controls, absolute protocol invocation required."""
from pathlib import Path
import copy,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
old=ROOT/'.runs/runtime056-native-controls-001/invalid';base=ROOT/'.runs/runtime056-native-controls-002/invalid';assert not base.exists()
assert p.sha(old/'protocol.json')=='6345bc4cd595ac49b4ecd626b70c44cf83f9468f520f4288c88476de5bad3b44'
failed=f.read_json(old/'enclosure/result.json');process=f.read_json(old/'enclosure/process.json')
assert failed['passed'] is False and failed['child_sha256'] is None and process['exit_code']==1 and process['cleanup_complete'] is True
assert 'FileNotFoundError' in (old/'enclosure/command.log').read_text()
plan=copy.deepcopy(f.read_json(old/'protocol.json'));assert not Path(plan['output']).exists()
plan['output']=str(Path(plan['output']).with_name('native7-comparison-control-runtime056-npth-invalid-002'));assert not Path(plan['output']).exists()
plan['pre_engine_invocation_correction']='Prior wrapper child could not read caller-relative protocol after cwd change. No Native executed. New namespace and absolute invocation only; controller/constraints/budgets/source/positive unchanged.'
base.mkdir(parents=True,mode=0o700);p.save_json(base/'protocol.json',plan)
p.save_json(base/'frozen.json',dict(schema=1,protocol_sha256=p.sha(base/'protocol.json'),controller_sha256=p.sha(Path(__file__)),executed=False,source_head=plan['source_head'],prior_failed_protocol_sha256=p.sha(old/'protocol.json'),prior_failed_enclosure_sha256=p.sha(old/'enclosure/result.json'),Native_repeated=False))
print(json.dumps(dict(protocol=str(base/'protocol.json'),sha256=p.sha(base/'protocol.json'),executed=False)))
