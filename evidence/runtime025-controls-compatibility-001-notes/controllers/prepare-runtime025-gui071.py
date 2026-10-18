"""Prepare fresh owned GUI inputs/launcher, preserving earlier sessions."""
import os, sys, json, shutil, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, preferences as pref, provenance as pv
from autorouter.runner import run
base=ROOT/'.runs/runtime-directory-025';runtime=base/'runtime'
cli=json.loads((base/'cli-workflow-001-run/execution.json').read_text());assert cli['passed']
tools=p.tool_manifest();source=ROOT/'.runs/task-copper-fixed-alias-native-004/source'
pins=json.loads((source.parent/'protocol.json').read_text())['source_hashes'];assert p.tree_hash(source)==pins
session=runtime/'.runs/gui-session071';session.mkdir()
for label in ('project','inspection'):shutil.copytree(source,session/label)
(session/'jobs').mkdir();assert p.tree_hash(session/'project')==p.tree_hash(session/'inspection')==pins
settings=pref.validate(dict(pref.DEFAULTS,scope='partial_completion',seconds=90))
p.save_json(session/'route-settings.json',settings)
launcher=runtime/'.runs/gui-launcher071'
env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
process=run([str(runtime/'.venv/bin/python'),'-B',str(runtime/'scripts/install_gui.py'),'--output',str(launcher)],cwd=runtime,env=env,log=session/'prepare-launcher.log',timeout=30,max_workdir_bytes=128*1024**2,max_group_rss_bytes=1024**3)
p.save_json(session/'prepare-launcher-process.json',process)
assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']
assert p.tool_manifest()==tools and p.tree_hash(source)==pins
record=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=tools['git_head'],runtime_manifest_sha256=p.sha(runtime/pv.MANIFEST),
 source=str(session/'project/owned1007-transport.kicad_pcb'),source_hashes=pins,inspection=str(session/'inspection/owned1007-transport.kicad_pro'),settings=settings,settings_path=str(session/'route-settings.json'),settings_sha256=p.sha(session/'route-settings.json'),jobs=str(session/'jobs'),launcher=str(launcher/'Launch Autorouter.command'),actual_GUI_qualified=False,
 scope='Fresh071 ordinary selected10.0.7 owned complete schematic/partial realgap/mixedlock/freevia/padless control. Pristine source never opened in editor. Use inspection copy for toolbar. Existing019/067,023/070GUI and024 failure evidence/preparations remain unchanged; new025 graphical controls unqualified. No live apply/undo or human certification.')
p.save_json(session/'prepared-state.json',record);print(json.dumps(record))
