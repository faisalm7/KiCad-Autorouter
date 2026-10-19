from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
head='3a71a124521ab1c051a9d772849d7913125518f0';assert p.tool_manifest()['git_head']==head
base=ROOT/'.runs/install-distribution-native-011';assert not base.exists();base.mkdir()
old=f.read_json(ROOT/'.runs/install-distribution-native-010/protocol.json');old.update(source_head=head,controller_sha256=p.sha(ROOT/'.runs/run-install-distribution-native-011.py'),output=str(ROOT/'.runs/runtime-directory-038'))
full=ROOT/'.runs/full-integration-183';data=f.read_json(full/'execution.json');assert data['passed'] and data['sources_unchanged'] and data['process']['cleanup_complete'] and not data['process']['log_truncated']
plan=f.read_json(full/'protocol.json');assert plan['tools']['git_head']==head
for name,digest in plan['source_sha256'].items():assert p.sha(ROOT/name)==digest
old.pop('full_integration180');old['full_integration183']=dict(execution_sha256=p.sha(full/'execution.json'),protocol_sha256=p.sha(full/'protocol.json'),gui_sha256=p.sha(ROOT/'autorouter/gui.py'))
old['source_files']={name:p.sha(ROOT/name) for name in old['source_files']}
old['scope']='Fresh curated selected7 runtime038 after v2 source-bound implicit-Default resolution and full183; unchanged minimal original smoke must run through actual Native observe/export/import/refill/check. No fullSCH/GUI/breadth qualification from smoke.'
p.save_json(base/'protocol.json',old);print(p.sha(base/'protocol.json'))
