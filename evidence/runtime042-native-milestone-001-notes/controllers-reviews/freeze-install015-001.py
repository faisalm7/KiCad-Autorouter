from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
head='82aaa3b750007ef2ffaafd367ffcb718aa93865e';assert p.tool_manifest()['git_head']==head
base=ROOT/'.runs/install-distribution-native-015';assert not base.exists();base.mkdir()
old=f.read_json(ROOT/'.runs/install-distribution-native-014/protocol.json');old.update(source_head=head,controller_sha256=p.sha(ROOT/'.runs/run-install-distribution-native-015.py'),output=str(ROOT/'.runs/runtime-directory-042'))
full=ROOT/'.runs/full-integration-187';data=f.read_json(full/'execution.json');assert data['passed'] and data['sources_unchanged'] and data['process']['cleanup_complete'] and not data['process']['log_truncated']
plan=f.read_json(full/'protocol.json');assert plan['tools']['git_head']==head
for name,digest in plan['source_sha256'].items():assert p.sha(ROOT/name)==digest
old.pop('full_integration186');old['full_integration187']=dict(execution_sha256=p.sha(full/'execution.json'),protocol_sha256=p.sha(full/'protocol.json'),gui_sha256=p.sha(ROOT/'autorouter/gui.py'))
old['source_files']={name:p.sha(ROOT/name) for name in old['source_files']}
old['scope']='Fresh curated selected7 runtime042 after the reporting-only parity declaration correction and full187. Producers report checked only after their own validation returns; no Native validation/admission, original-rule, protection or cancellation guard changes. Unchanged canonical smoke must run actual Native observe/export/import/refill/check. Six-stage, actual GUI and breadth qualification remain separate; immutable041 evidence and the closed-admission reporting defect stay historical.'
p.save_json(base/'protocol.json',old);print(p.sha(base/'protocol.json'))
