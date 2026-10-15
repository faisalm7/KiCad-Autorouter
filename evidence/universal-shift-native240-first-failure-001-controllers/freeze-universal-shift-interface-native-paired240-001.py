from pathlib import Path
import datetime,sys,json,subprocess
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from scripts import experiment_quality as q,experiment_portfolio as portfolio
P=R/'.runs/universal-shift-interface-native-paired240-001-protocol.json';assert not P.exists()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=R)
s=json.loads((R/'.local-backups/universal-shift-native-all-integration-001/.runs/universal-shift-interface-native-paired240-001-protocol.template.json').read_text())
board,family=q.selected_source('universal-shift-interface');frozen=portfolio.freeze(board);frozen['files_sha256']['scripts/experiment_paired.py']=p.sha(R/'scripts/experiment_paired.py')
s.update(status='frozen',tools=frozen['tools'],git_head=frozen['tools']['git_head'],freeze=frozen,frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),freeze_controller_sha256=p.sha(Path(__file__)))
for source,pin in [('wrapper_source','wrapper_sha256'),('reader_source','reader_sha256'),('reader_controller_source','reader_controller_sha256')]:s[pin]=p.sha(Path(s[source]))
assert s['source']==str(board) and s['family']==family and s['original_source_sha256']==p.tree_hash(board.parent)
for name,pin in s['complete_source_files_sha256'].items():assert p.sha(R/name)==pin,name
for name,pin in s['common_prerequisites']['pins'].items():assert p.sha(R/name)==pin,name
for item in s['common_prerequisites']['stages']:assert p.sha(R/item['path'])==item['sha256'],item['path']
p.save_json(P,s);print(json.dumps(dict(git_head=s['git_head'],protocol_sha256=p.sha(P),source_file_count=len(s['original_source_sha256']),freeze_code_files=len(frozen['files_sha256']),status=s['status'])))
