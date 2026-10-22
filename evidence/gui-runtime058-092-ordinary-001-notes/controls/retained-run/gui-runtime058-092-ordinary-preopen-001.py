from pathlib import Path
import json,sys,datetime
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-058/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p, review_export as ex, placement_clearance as io
base=runtime/'.runs/gui-session092';w=base/'jobs/autorouter-gui-272e1539f82849a1bf4d56f229931c2f';prepared=json.loads((base/'prepared-state.json').read_bytes())
assert p.sha(runtime/'runtime-distribution.json')==prepared['runtime_manifest_sha256']=='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74'
assert p.tree_hash(Path(prepared['source']).parent)==prepared['roles']['ordinary-alias2Cu']['source_hashes']
with p.validation_readback_session():
 route=p.check_result(w/'route/result.json');export=ex.check_export(w/'export/export.json')
assert route['current'] and export['current'] and export['export_accepted']
snapshot=base/'preopen-ordinary-export-001';snapshot.mkdir(mode=0o700)
for name,raw in io.inventory(w/'export',contents=True).items():
 target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as stream:stream.write(raw)
assert p.tree_hash(snapshot)==p.tree_hash(w/'export')
p.save_json(base/'preopen-ordinary-001.json',dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='point-in-time-current-export-before-editor-open-v1',route=route,export=export,snapshot=str(snapshot),snapshot_hashes=p.tree_hash(snapshot),source_unchanged=True,human_review=False,actual_GUI_qualified=False,scope='Existing preopen capture pattern only. Actual central readers passed at original paths before copying. Later editor metadata changes must still refuse current export; this snapshot is retained historical proof, not renewed authority.'))
print(json.dumps({'route_current':True,'export_current':True,'snapshot_files':len(p.tree_hash(snapshot)),'candidate_sha256':export['candidate_sha256']}))
