"""Finite pinned public source reads only; no source/dependency execution."""
from pathlib import Path
import hashlib,json,time,urllib.request
OUT=Path(__file__).resolve().parent
COMMIT='0feeca2a807f428ad2b3fa7c1e39625cb769f02c'
PATHS=('common/project/project_local_settings.cpp','include/project/project_local_settings.h','pcbnew/zone_filler.cpp','pcbnew/tools/zone_filler_tool.cpp','pcbnew/pcb_edit_frame.cpp')
TOTAL=1024*1024;used=0;rows=[]
for name in PATHS:
 url='https://raw.githubusercontent.com/KiCad/kicad-source-mirror/'+COMMIT+'/'+name
 request=urllib.request.Request(url,headers={'User-Agent':'local-kicad-source-audit/1'})
 with urllib.request.urlopen(request,timeout=20) as response:
  assert response.status==200 and response.url==url
  raw=response.read(min(512*1024,TOTAL-used)+1)
 assert 0<len(raw)<=min(512*1024,TOTAL-used)
 raw.decode('utf-8');used+=len(raw);path=OUT/'source'/name;path.parent.mkdir(parents=True,exist_ok=True)
 assert not path.exists();path.write_bytes(raw)
 rows.append({'path':name,'url':url,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()})
(OUT/'source-receipt.json').write_text(json.dumps({'schema':1,'commit':COMMIT,'files':rows,'bytes':used,'file_limit':len(PATHS),'total_byte_limit':TOTAL,'scope':'Pinned KiCad primary text only; no execution'},indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':used}))
