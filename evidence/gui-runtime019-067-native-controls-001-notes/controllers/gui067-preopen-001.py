from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; runtime=ROOT/'.runs/runtime-directory-019/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p, review_export as ex, placement_clearance as io
base=runtime/'.runs/gui-session067';w=base/'jobs/autorouter-gui-2fc011e6ac074640919edaa66da0e843';launch=json.loads((base/'launch.json').read_bytes())
assert p.tree_hash(Path(launch['source']).parent)==launch['source_sha256']
with p.validation_readback_session():
    route=p.check_result(w/'route/result.json'); export=ex.check_export(w/'export/export.json')
assert route['current'] and export['current']
snapshot=base/'resume-001/preopen-snapshot-001';snapshot.mkdir()
for name,raw in io.inventory(w/'export',contents=True).items():
    target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
assert p.tree_hash(snapshot)==p.tree_hash(w/'export')
p.save_json(base/'resume-001/preopen-001.json',dict(schema=1,route=route,export=export,snapshot=str(snapshot),snapshot_hashes=p.tree_hash(snapshot),source_unchanged=True,human_review=False))
print(json.dumps({'route_current':True,'export_current':True,'snapshot_files':len(p.tree_hash(snapshot))}))
