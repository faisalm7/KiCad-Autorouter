"""Exact raw/public floor evidence subset verification; no native work."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=0;outcomes=[]
for name in ('board-floor-geometry-001','board-floor-geometry-002','board-floor-forced-via-001'):
    raw=ROOT/'.runs'/name;public=ROOT/'evidence'/name;manifest=json.loads((public/'files.json').read_text());scope=json.loads((public/'scope.json').read_text())
    assert scope['source']==str(raw);checks+=1
    rows=manifest['files'];assert len({r['path'] for r in rows})==len(rows);checks+=1
    expected=set()
    for f in raw.rglob('*'):
        assert not f.is_symlink();checks+=1
        if f.is_file() and not set(f.relative_to(raw).parts)&{'kicad-config','tmp','engine-config'}:expected.add(str(f.relative_to(raw)))
    assert {r['path'] for r in rows}==expected;checks+=1
    actual={str(p.relative_to(public)) for p in public.rglob('*') if p.is_file()}
    assert actual==expected|{'files.json','scope.json'};checks+=1
    for row in rows:
        a=raw/row['path'];b=public/row['path'];assert not b.is_symlink() and a.read_bytes()==b.read_bytes() and sha(a)==row['sha256'] and a.stat().st_size==row['bytes'];checks+=1
    assert scope['files']==len(rows) and scope['bytes']==sum(r['bytes'] for r in rows);checks+=1
    outcomes.append({'run':name,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'raw_status':json.loads((raw/'summary.json').read_text())['status'],'raw_controls_passed':json.loads((raw/'summary.json').read_text())['controls_passed'],'raw_manifest_sha256':sha(public/'files.json')})
result={'passed':True,'checks':checks,'native_executed':False,'subsets':outcomes,'scope':'All selected raw copies exact; generated files.json/scope.json checked as metadata, not claimed raw copies.'}
(OUT/'public-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
