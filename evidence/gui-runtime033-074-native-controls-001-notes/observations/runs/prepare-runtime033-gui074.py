"""Fresh GUI inputs/launcher using existing preparation and exact stable033."""
from pathlib import Path
import sys,os,json,shutil,datetime
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-033/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,preferences as pref,provenance as pv,config as c
from autorouter.runner import run
assert c.ROOT==runtime and c.NATIVE_VERSION=='10.0.7'
assert p.sha(runtime/pv.MANIFEST)=='115c881aa04a34bf642c57d5af312fe692d1aff013bed095caa3856a614f3987'
for name in ('full-integration-176','install-distribution-native-006'):
 assert json.loads((ROOT/'.runs'/name/'execution.json').read_bytes())['passed']
tools=p.tool_manifest();assert tools['git_head']=='a476a0a0647bc51889d291e3e6e2598f4ec24370'
query=json.loads((ROOT/'.runs/runtime033-method-material-002/tools-defaults.json').read_bytes());assert tools==query['tools']
source=ROOT/'.runs/task-copper-fixed-alias-native-004/source'
pins=json.loads((ROOT/'.runs/runtime033-ordinary-partial2Cu-001/protocol.json').read_bytes())['source_hashes']
assert p.tree_hash(source)==pins and shutil.disk_usage(ROOT).free>2*1024**3
session=runtime/'.runs/gui-session074';launcher=runtime/'.runs/gui-launcher074'
assert not session.exists() and not launcher.exists();session.mkdir(mode=0o700)
for label in ('project','inspection'):shutil.copytree(source,session/label)
(session/'jobs').mkdir();assert p.tree_hash(session/'project')==p.tree_hash(session/'inspection')==pins
settings=pref.validate(dict(pref.DEFAULTS,scope='partial_completion',seconds=90));p.save_json(session/'route-settings.json',settings)
env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN')}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([str(runtime/'.venv/bin/python'),'-B',str(runtime/'scripts/install_gui.py'),'--output',str(launcher)],cwd=session,env=env,log=session/'prepare-launcher.log',timeout=30,max_workdir_bytes=128*1024**2,max_group_rss_bytes=1024**3)
p.save_json(session/'prepare-launcher-process.json',process)
assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
assert p.tool_manifest()==tools and p.tree_hash(source)==pins
record=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=tools['git_head'],runtime_manifest_sha256=p.sha(runtime/pv.MANIFEST),source=str(session/'project/owned1007-transport.kicad_pcb'),source_hashes=pins,inspection=str(session/'inspection/owned1007-transport.kicad_pro'),settings=settings,settings_path=str(session/'route-settings.json'),settings_sha256=p.sha(session/'route-settings.json'),jobs=str(session/'jobs'),launcher=str(launcher/'Launch Autorouter.command'),actual_GUI_qualified=False,scope='Current033 fresh074 owned complete schematic/partial realgap/protected4. Pristine source never opened; inspection copy only in editor. Historical026GUI and prepared029GUI073 preserved. Actual074controls remain pending; no liveapply/undo orhuman certification.')
p.save_json(session/'prepared-state.json',record);print(json.dumps(record))
