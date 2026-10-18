from pathlib import Path
import json,shutil,sys,datetime
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-033/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,preferences as pref
base=runtime/'.runs/gui-session074';pop=json.loads((ROOT/'.runs/runtime033-interf-current-comparison-001/population.json').read_bytes());source=Path(pop['source']);assert p.tree_hash(source.parent)==pop['source_hashes'];assert shutil.disk_usage(ROOT).free>2*1024**3
out=base/'cancel-control-001';out.mkdir();shutil.copytree(source.parent,out/'project');assert p.tree_hash(out/'project')==pop['source_hashes']
settings=pref.validate(dict(pref.DEFAULTS,scope='whole_board',seconds=90));p.save_json(out/'route-settings.json',settings)
p.save_json(out/'prepared.json',dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=str(out/'project'/source.name),source_hashes=pop['source_hashes'],source_rights=pop['source_rights'],settings=settings,runtime_manifest_sha256=pop['runtime_manifest_sha256'],scope='Actual GUI cancellation control only; exposed licensed officialInterf gives observable engine interval. No additional completion-quality comparison or new failure-class investigation. Original source retained; no positive accepted result expected. Verify owned current process ancestry before actual GUI Cancel.'))
print(json.dumps(dict(source=str(out/'project'/source.name),settings=settings)))
