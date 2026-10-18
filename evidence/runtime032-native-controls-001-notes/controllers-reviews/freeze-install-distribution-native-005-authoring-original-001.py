from pathlib import Path
import sys,json,datetime,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
suite=json.loads((ROOT/'.runs/full-integration-174/execution.json').read_text());assert suite['passed'] and suite['sources_unchanged']
old=json.loads((ROOT/'.runs/install-distribution-native-004/protocol.json').read_text())
files={name:p.sha(ROOT/name) for name in old['source_files']}
full=json.loads((ROOT/'.runs/full-integration-174/protocol.json').read_text())
assert all(pin==full['source_sha256'][name] for name,pin in files.items() if name.startswith('autorouter/'))
head=p.tool_manifest()['git_head'];output=ROOT/'.runs/runtime-directory-032';assert not output.exists()
assert shutil.disk_usage(ROOT).free>3*1024**3
plan=dict(old,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=head,source_files=files,controller_sha256=p.sha(ROOT/'.runs/run-install-distribution-native-005.py'),output=str(output),free_bytes_before=shutil.disk_usage(ROOT).free,scope='Fresh existing curated distribution/native installer for committed comparison-v2 source/full174 modules, new032 selected10.0.7; owned doctor/Native Route/check only. Later v2/ordinary/GUI results require own actual controls. No cleanOS/relocation/Windows/release claim.')
base=ROOT/'.runs/install-distribution-native-005';base.mkdir();q=base/'protocol.json'
with q.open('x') as stream:json.dump(plan,stream,indent=2);stream.write('\n')
print(json.dumps({'protocol':str(q),'sha256':p.sha(q),'source_head':head,'freeze_only':True}))
