"""Bounded primary-source text/metadata fetches, no source execution."""
from pathlib import Path
import hashlib,json,urllib.request,urllib.error
OUT=Path(__file__).resolve().parent

def fetch(url,name):
    ledger=OUT/'fetch-receipt.json'
    rows=json.loads(ledger.read_text()) if ledger.exists() else []
    assert len(rows)<14
    used=sum(r.get('bytes',0) for r in rows);limit=min(256*1024,1024*1024-used);assert limit>0
    assert url.startswith(('https://api.github.com/repos/KiCad/kicad-source-mirror/','https://raw.githubusercontent.com/KiCad/kicad-source-mirror/'))
    path=OUT/name;assert path.is_relative_to(OUT) and not path.exists();path.parent.mkdir(parents=True,exist_ok=True)
    row={'url':url,'path':name,'status':None,'max_bytes':limit}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'local-kicad-source-audit/1'}),timeout=20) as response:
            row['status']=response.status;assert response.url==url and response.status==200
            raw=response.read(limit+1);assert 0<len(raw)<=limit;raw.decode('utf-8')
        path.write_bytes(raw);row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
    except Exception as exc:
        row['error']=type(exc).__name__+': '+str(exc);rows.append(row);ledger.write_text(json.dumps(rows,indent=2)+'\n');raise
    rows.append(row);ledger.write_text(json.dumps(rows,indent=2)+'\n');return raw
