"""Current050 binding around shared preopen readers, bounded inventory and final-event guards.
Preserve exact pre-editor export bytes; no routing/DRC solve or GUI opening here.
"""
from pathlib import Path
import datetime,json,re,sys,time
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-050/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,review_export as ex,placement_clearance as io,local_settings as local,strategy
start=time.monotonic();role,workspace,label=sys.argv[1:]
assert role in ('ordinary-alias2Cu','improve-fractional') and re.fullmatch('autorouter-gui-[0-9a-f]{32}',workspace) and re.fullmatch('[a-z0-9-]{1,48}',label)
base=runtime/'.runs/gui-session086';w=base/'jobs'/workspace;prepared=f.read_json(base/'prepared-state.json')
assert p.sha(base/'prepared-state.json')=='59243bac41824b5efa2a336a53d3ff59bd6d725bf61a9686d3315575fe74a7ae'
assert prepared['source_head']=='aa0072c6b3d8090de2603e5ecb42a95968fb873b'
assert p.sha(runtime/'runtime-distribution.json')==prepared['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
assert p.sha(base/'protocol-required-001.json')==prepared['protocol_required_sha256']=='622e76392b4aa72b7eceab24ce471046bfc1a3f90c3635900bc1c5bcd23e83e0'
protocol=f.read_json(base/'protocol-required-001.json');assert protocol['roles']==prepared['roles'] and protocol['source_head']==prepared['source_head'] and protocol['runtime_manifest_sha256']==prepared['runtime_manifest_sha256']
tools=p.tool_manifest();assert tools==prepared['tools'];declared=prepared['roles'][role];source=Path(declared['source']);hashes=declared['source_hashes']
assert io.inventory(source.parent)==io.inventory(Path(declared['original_source']).parent)==hashes
assert f.read_json(w/'settings.json')==declared['settings']
route=f.read_json(w/'route/result.json');exported=f.read_json(w/'export/export.json')
assert route['source']==str(source) and route['source_hashes']==exported['source_hashes']==hashes
assert route['accepted'] is True and exported['export_accepted'] is True and route['candidate_sha256']==exported['candidate_sha256']
assert route['tools']==exported['tools']==tools and route['schematic_parity']==exported['schematic_parity']=='checked by final native DRC'
assert [exported['native'][key] for key in ('opens','blocking','warnings','exclusions')]==([0,0,0,0] if role=='ordinary-alias2Cu' else [0,0,6,0])
with p.validation_readback_session():
 checked=p.check_result(w/'route/result.json');checked_export=ex.check_export(w/'export/export.json')
assert checked['current'] is True and checked_export['current'] is True
control=base/('preopen-'+label);assert not control.exists();control.mkdir(mode=0o700);snapshot=control/'export';snapshot.mkdir()
raw=io.inventory(w/'export',contents=True,max_bytes=64*1024**2,max_files=8000,max_entries=16000)
for name,content in raw.items():
 path=snapshot/name;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(content)
assert io.inventory(snapshot)==io.inventory(w/'export')
assert io.inventory(source.parent)==hashes and p.tool_manifest()==tools
snapshot_hashes=io.inventory(snapshot);settings_pin=p.sha(w/'settings.json');controller_pin=p.sha(Path(__file__))
packets=strategy.native7_packets(w/'route',route) if role=='improve-fractional' else [(w/'route',route)]
packets.append((w/'export/validation',exported));local.check_final_events(packets,p.c.CLI)
receipt=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime='050',session='086',role=role,workspace=str(w),source_head=prepared['source_head'],runtime_manifest_sha256=prepared['runtime_manifest_sha256'],route=checked,export=checked_export,source=str(source),source_hashes=hashes,source_unchanged=True,settings_sha256=settings_pin,snapshot=str(snapshot),snapshot_hashes=snapshot_hashes,controller_sha256=controller_pin,actual_GUI_opening=False,human_review=False,scope='Central current production readers plus exact pre-editor export snapshot and final-event guards. Retained Native/field workers may be checked by central readers; no routing or newDRC solve and no actual opening implied.',sampled_wall_seconds=time.monotonic()-start)
p.save_json(control/'preopen.json',receipt);print(json.dumps(dict(receipt=str(control/'preopen.json'),snapshot_files=len(receipt['snapshot_hashes']),route_current=True,export_current=True)))
