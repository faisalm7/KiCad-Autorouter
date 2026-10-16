from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime-directory-007/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,gui
from scripts import install_gui
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
tools=p.tool_manifest();assert tools['git_head']=='e01676441ba967122b4e8e919c6a7de48ad5a8d0'
setup=json.loads((ROOT/'.runs/runtime-directory-007/setup.json').read_text())
original=Path(setup['source']).parent;assert p.tree_hash(original)==setup['source_hashes']
base=runtime/'.runs/gui-session058';base.mkdir();source=base/'project';inspection=base/'inspection'
source.mkdir();inspection.mkdir();(base/'jobs').mkdir()
for name,expected in setup['source_hashes'].items():
 raw=(original/name).read_bytes()
 for directory in (source,inspection):(directory/name).write_bytes(raw)
assert p.tree_hash(source)==setup['source_hashes'] and p.tree_hash(inspection)==setup['source_hashes']
launcher=install_gui.prepare(runtime/'.runs/gui-launcher058')
for name,module in tuple(sys.modules.items()):
 if name.split('.')[0] in {'autorouter','scripts'} and getattr(module,'__file__',None):assert Path(module.__file__).resolve().is_relative_to(runtime),name
record=dict(schema=1,source=str(source/'owned-four-copper-forced-inner.kicad_pcb'),source_sha256=p.tree_hash(source),inspection=str(inspection/'owned-four-copper-forced-inner.kicad_pro'),source_git_head=tools['git_head'],source_provenance=tools['source_provenance'],gui_sha256=p.sha(Path(gui.__file__)),installer_sha256=p.sha(Path(install_gui.__file__)),launcher=launcher,installed_module_context_verified=True,human_review=False)
(base/'launch.json').write_text(json.dumps(record,indent=2)+'\n')
assert p.tool_manifest()==tools
print(json.dumps({k:record[k] for k in ('source','inspection','source_git_head','gui_sha256','installer_sha256')}))
