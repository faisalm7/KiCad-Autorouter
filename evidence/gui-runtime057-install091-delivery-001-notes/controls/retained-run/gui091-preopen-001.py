"""Fresh-root057 binding for the shared production readers and bounded snapshot.

Same pre-editor preservation procedure as gui090-preopen-001; no new DRC solve.
"""
from pathlib import Path
import datetime,json,sys,time
START=time.monotonic()
ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime057 fresh install 001'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as ex,placement_clearance as io,local_settings as local
base=runtime/'.runs/gui-session091'
w=base/'jobs/autorouter-gui-cf6247f87e384c68bda447765c7ca1f3'
prepared=f.read_json(base/'prepared-state.json')
assert p.sha(base/'prepared-state.json')=='903642f70376af8e6dc8ff365183b244d48598ddc7ad9a90676e4507c96a4de8'
assert p.sha(runtime/'runtime-distribution.json')==prepared['runtime_manifest_sha256']=='b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51'
tools=p.tool_manifest();assert tools==prepared['tools']
source=Path(prepared['source']);hashes=prepared['source_hashes']
assert io.inventory(source.parent)==io.inventory(Path(prepared['original_source']).parent)==hashes
assert f.read_json(w/'settings.json')==prepared['settings']
route=f.read_json(w/'route/result.json');exported=f.read_json(w/'export/export.json')
assert route['source']==str(source) and route['source_hashes']==exported['source_hashes']==hashes
assert route['accepted'] is True and exported['export_accepted'] is True and route['candidate_sha256']==exported['candidate_sha256']
assert route['tools']==exported['tools']==tools and route['schematic_parity']==exported['schematic_parity']=='checked by final native DRC'
assert [exported['native'][key] for key in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
with p.validation_readback_session():
    checked=p.check_result(w/'route/result.json');checked_export=ex.check_export(w/'export/export.json')
assert checked['current'] is True and checked_export['current'] is True
control=base/'preopen-001';assert not control.exists();control.mkdir(mode=0o700)
snapshot=control/'export';snapshot.mkdir()
raw=io.inventory(w/'export',contents=True,max_bytes=64*1024**2,max_files=8000,max_entries=16000)
for name,content in raw.items():
    path=snapshot/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(content)
assert io.inventory(snapshot)==io.inventory(w/'export')
assert io.inventory(source.parent)==hashes and p.tool_manifest()==tools
local.check_final_events([(w/'route',route),(w/'export/validation',exported)],p.c.CLI)
receipt=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime=str(runtime),session='091',workspace=str(w),source_head=prepared['source_head'],runtime_manifest_sha256=prepared['runtime_manifest_sha256'],route=checked,export=checked_export,source=str(source),source_hashes=hashes,source_unchanged=True,settings_sha256=p.sha(w/'settings.json'),snapshot=str(snapshot),snapshot_hashes=io.inventory(snapshot),controller_sha256=p.sha(Path(__file__)),actual_GUI_opening=False,human_review=False,scope='Shared production readers and exact pre-editor snapshot/final-event guards. Retained Native/field process proofs may be checked; no routing or new DRC solve and no opening implied.',sampled_wall_seconds=time.monotonic()-START)
p.save_json(control/'preopen.json',receipt)
print(json.dumps(dict(receipt=str(control/'preopen.json'),snapshot_files=len(receipt['snapshot_hashes']),route_current=True,export_current=True)))
