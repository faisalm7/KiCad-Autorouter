from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
head='e5593ae129e88c719c9066d0464edb6aba0df487';assert p.tool_manifest()['git_head']==head
base=ROOT/'.runs/install-distribution-native-013';assert not base.exists();base.mkdir()
old=f.read_json(ROOT/'.runs/install-distribution-native-012/protocol.json');old.update(source_head=head,controller_sha256=p.sha(ROOT/'.runs/run-install-distribution-native-013.py'),output=str(ROOT/'.runs/runtime-directory-040'))
full=ROOT/'.runs/full-integration-185';data=f.read_json(full/'execution.json');assert data['passed'] and data['sources_unchanged'] and data['process']['cleanup_complete'] and not data['process']['log_truncated']
plan=f.read_json(full/'protocol.json');assert plan['tools']['git_head']==head
for name,digest in plan['source_sha256'].items():assert p.sha(ROOT/name)==digest
old.pop('full_integration184');old['full_integration185']=dict(execution_sha256=p.sha(full/'execution.json'),protocol_sha256=p.sha(full/'protocol.json'),gui_sha256=p.sha(ROOT/'autorouter/gui.py'))
old['source_files']={name:p.sha(ROOT/name) for name in old['source_files']}
old['scope']='Fresh curated selected7 runtime040 after the bounded source-all two-copper signal/display identity correction and full185; unchanged minimal canonical smoke must run through actual Native observe/export/import/refill/check. No source/DSN renaming, type/mask/class widening or NUS mixed/power support; alias-specific Native controls, fullSCH, GUI and breadth qualification remain separate from this smoke.'
p.save_json(base/'protocol.json',old);print(p.sha(base/'protocol.json'))
