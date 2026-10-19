"""Pure component replay on retained failed040 data; no candidate admission."""
from pathlib import Path
import copy,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import padless_alias as a,netclass_native as n,pipeline as p,sexpr as sx
out=ROOT/'.runs/runtime-directory-040/runtime/.runs/ordinary-alias2Cu-003';workflow=json.loads((out/'result.json').read_bytes());work=Path(workflow['workspace'])/'route';receipt=json.loads((work/'result.json').read_bytes());assert receipt['accepted'] is False and receipt['status']=='invalidated'
paths=a.artifact_paths(work/'task.dsn');tracked=[work/'result.json',work/'native.dsn',work/'export-netclasses.json',*paths.values()];before={str(path):p.sha(path) for path in tracked};proof=json.loads(paths['proof'].read_bytes());raw=paths['source_copy'].read_bytes();mapping=json.loads((work/'export-netclasses.json').read_bytes());identity=n.check_source_all_layers(mapping,sx.parse(raw.decode()));expected=[dict(name=row['display_name'],canonical=row['canonical'],type=row['type']) for row in identity]
a._check_observation(proof['observation'],paths,raw,(work/'native.dsn').read_bytes(),proof['binding'],layers=expected)
bad=copy.deepcopy(proof['observation'])
for event in bad['events']:
 rows=event['observation']['layers_text']['layers'];rows[0]['name'],rows[1]['name']=rows[1]['name'],rows[0]['name']
try:a._check_observation(bad,paths,raw,(work/'native.dsn').read_bytes(),proof['binding'],layers=expected)
except p.Rejected as exc:negative=str(exc)
else:raise AssertionError('consistently swapped actual observations must refuse')
assert before=={str(path):p.sha(path) for path in tracked}
result=dict(schema=1,component_replay_passed=True,all_four_actual_phases=True,consistently_swapped_negative=negative,Native_executed=False,full_acceptance_executed=False,accepted=False,runtime040_status_unchanged='invalidated',retained_input_sha256=before,current_source_sha256={name:p.sha(ROOT/name) for name in ('autorouter/padless_alias.py','autorouter/netclass_native.py','autorouter/layer_policy.py')},scope='Pure observation-census/hash/restoration component check on actual failed040 Native bytes. Does not rerun Native, repair or accept040, establish new GUI qualification or replace fresh changed-code validation.')
p.save_json(ROOT/'.runs/alias-census-retained040-replay-001.json',result);print(json.dumps(result))
