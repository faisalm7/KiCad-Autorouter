"""Byte-check only the declared selected public subset against raw originals."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
PUBLIC=ROOT/'evidence/pic-severity-controls-002';RUN=ROOT/'.runs/pic-severity-controls-002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((PUBLIC/'public-copy.json').read_text());checked={};total=0
external={'execution.json':ROOT/'.runs/pic-severity-controls-002-execution.json','command.log':ROOT/'.runs/pic-severity-controls-002-command.log','run.py':ROOT/'.runs/run-pic-severity-controls-002.py'}
for rel,pin in meta['files'].items():
    public=PUBLIC/rel;raw=external.get(rel,RUN/rel)
    assert not public.is_symlink() and public.read_bytes()==raw.read_bytes()
    assert public.stat().st_size==pin['bytes'] and sha(public)==pin['sha256']
    checked[rel]=pin;total+=pin['bytes']
assert len(checked)==meta['file_count']==76 and total==meta['total_bytes']==573291
assert len(meta['omitted_generated_defaults'])==48
for rel in meta['omitted_generated_defaults']:assert not (PUBLIC/rel).exists() and (RUN/rel).is_file()
value={'schema':1,'passed':True,'file_count':len(checked),'total_bytes':total,'public_manifest_sha256':sha(PUBLIC/'public-copy.json'),'copied_bytes_match_raw':True,'omitted_generated_default_count':48,'scope':'Only the76 copied raw files declared by public-copy.json. Generated public notices/manifest are separately authored and not claimed to be raw copies. No raw files edited.','files':checked}
(OUT/'public-copy-audit.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'passed':True,'file_count':len(checked),'bytes':total}))
