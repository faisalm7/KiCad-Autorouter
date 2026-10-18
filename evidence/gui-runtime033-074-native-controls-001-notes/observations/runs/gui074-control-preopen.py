"""Retain a GUI fault control's current proof before the deliberate mutation.

Uses the production readers and bounded inventory, following gui067-preopen-001.
This controller is not an additional validator or a Native test.
"""
from pathlib import Path
import json,sys,time
ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime-directory-033/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p, review_export as ex, placement_clearance as io
start=time.monotonic();label,workspace=sys.argv[1:]
assert label in ('source','settings','export')
base=runtime/'.runs/gui-session074';control=base/'freshness-controls-001'/label
w=base/'jobs'/workspace
protocol=json.loads((control.parent/'protocol-frozen-001.json').read_bytes())
assert p.tree_hash(control/'project')==protocol['source_hashes']
with p.validation_readback_session():
    route=p.check_result(w/'route/result.json')
    exported=ex.check_export(w/'export/export.json')
assert route['current'] is True and exported['current'] is True
record=json.loads((w/'route/result.json').read_bytes())
assert Path(record['source']).parent==control/'project'
snapshot=control/'preopen-export';snapshot.mkdir()
for name,raw in io.inventory(w/'export',contents=True).items():
    target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
assert p.tree_hash(snapshot)==p.tree_hash(w/'export')
p.save_json(control/'preopen-001.json',dict(schema=1,workspace=str(w),route=route,export=exported,snapshot=str(snapshot),snapshot_hashes=p.tree_hash(snapshot),source_hashes=protocol['source_hashes'],human_review=False,wall_seconds=time.monotonic()-start))
print(json.dumps(dict(label=label,route_current=True,export_current=True,snapshot_files=len(p.tree_hash(snapshot)))))
