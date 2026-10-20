"""Reuse the unchanged finite Native-control enclosure after an actual positive."""
from pathlib import Path
import sys,shutil,ast
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
runtime=R/'.runs/runtime-directory-049/runtime';prep=f.read_json(runtime.parent/'preparation.json')
assert prep['source_head']=='6e2357f975554478c2ba9fa35f18fdc3c1d194f9' and p.sha(runtime/'runtime-distribution.json')==prep['manifest_sha256']
positive=R/'.runs/runtime049-native-qualification-001/improve-pour-only';result=f.read_json(positive/'execution.json');assert result['controls_passed'] and result['workflow_delivered']
child=f.read_json(Path(result['child_receipt']));workspace=Path(child['workspace']);receipt=workspace/'route/result.json';data=f.read_json(receipt)
assert data['accepted'] and data['status']=='routing_accepted' and p.sha(Path(result['child_receipt']))==result['child_sha256']
source=Path(data['source']);assert p.tree_hash(source.parent)==data['source_hashes']
base=R/'.runs/runtime049-native-controls-001';base.mkdir(mode=0o700)
enclosure=R/'.runs/enclose-native7-independent-control-004.py'
for name,helper in [('invalid','qualify-runtime044-safety-001.py'),('cancel','qualify-runtime044-cancel-001.py'),('reserved-return','qualify-native7-reserved-return-001.py')]:
 original=R/'.runs'/helper;ast.parse(original.read_text());controller=runtime/'.runs'/helper;assert not controller.exists()
 with controller.open('xb') as stream:stream.write(original.read_bytes())
 folder=base/name;folder.mkdir();out=runtime/'.runs'/('native7-comparison-control-runtime049-'+name+'-001');assert not out.exists()
 plan=dict(schema=1,kind='runtime049-single-improve-'+name+'-control-v1',runtime=str(runtime),runtime_manifest_sha256=prep['manifest_sha256'],source_head=prep['source_head'],controller=str(controller),controller_sha256=p.sha(controller),controller_args=[],pass_key='control_passed',enclosure_sha256=p.sha(enclosure),output=str(out),whole_wall_full_cpu_seconds=135,receipt=str(receipt),administration=str(R),source=str(source),source_hashes=data['source_hashes'],prerequisites={str(path):p.sha(path) for path in (positive/'execution.json',Path(result['child_receipt']),receipt)},freezer_sha256=p.sha(Path(__file__)),scope='Fresh runtime049 two bounded diagnostic or cancellation controls only. Shared existing enclosure135s includes a controller120s cap; all Native workers use original source/rules and source remains immutable. No actual GUI, population false-acceptance, electrical, all-phase cancellation or quality claim.')
 if name=='reserved-return':plan.update(method_seconds=40,required_return_reserve_seconds=25,scope='One natural40s CLI near-reserve incumbent-return control on the unchanged qualified pour-only source. GUI minimum90 is unchanged; <=4s wall work headroom is not necessarily expiry. Failed/unobserved events retained; no tuning or automatic retry. Existing135outer/120innercaps and complete real Native acceptance remain.')
 p.save_json(folder/'protocol.json',plan);print(name,p.sha(folder/'protocol.json'))
