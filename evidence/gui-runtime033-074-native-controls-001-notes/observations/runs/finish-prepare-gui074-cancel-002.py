from pathlib import Path
import sys,json,datetime
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-033/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,preferences as pref
base=runtime/'.runs/gui-session074';pop=json.loads((ROOT/'.runs/runtime033-interf-current-comparison-001/population.json').read_bytes());source=Path(pop['source']);out=base/'cancel-control-001'
assert p.tree_hash(out/'project')==p.tree_hash(source.parent)==pop['source_hashes']
assert not (out/'route-settings.json').exists() and not (out/'prepared.json').exists()
settings=pref.validate(dict(pref.DEFAULTS,scope='whole_board_unlocked_routing',seconds=90));p.save_json(out/'route-settings.json',settings)
p.save_json(out/'prepared.json',dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=str(out/'project'/source.name),source_hashes=pop['source_hashes'],source_rights=pop['source_rights'],settings=settings,runtime_manifest_sha256=pop['runtime_manifest_sha256'],authoring_correction='Initial preparation copied original project but refused invalid scope whole_board before any Native/GUI job. Preserved original script and copy; completed only missing settings/receipt using documented whole_board_unlocked_routing.',scope='Actual GUI cancellation control only. Exposed licensed officialInterf gives observable engine interval. No new quality experiment. Original source retained; no positive accepted result expected. Verify owned process ancestry before actual GUI Cancel.'))
print(json.dumps(dict(source=str(out/'project'/source.name),settings=settings)))
