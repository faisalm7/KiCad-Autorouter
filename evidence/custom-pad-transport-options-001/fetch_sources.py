"""Five exact pinned primary-source reads; no executable code from responses is run."""
import hashlib,json,time,urllib.request
from pathlib import Path
OUT=Path(__file__).resolve().parent
COMMIT='b647a2f824cfbc54bc4dcaee71b03b7cd945eb76'
PATHS=['src/main/java/app/freerouting/io/specctra/parser/Wiring.java','src/main/java/app/freerouting/io/specctra/parser/Structure.java','src/main/java/app/freerouting/board/model/items/ConductionArea.java','src/main/java/app/freerouting/io/specctra/parser/Shape.java','src/main/java/app/freerouting/board/facade/BasicBoard.java']
records=[];total=0
for path in PATHS:
 url='https://raw.githubusercontent.com/freerouting/freerouting/'+COMMIT+'/'+path;t=time.monotonic();row={'url':url,'commit':COMMIT,'source_path':path}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'KiCad-Autorouter-local-source-research'}),timeout=20) as r:
   remaining=1024**2-total;raw=r.read(remaining+1)
   if len(raw)>remaining:raise ValueError('1MiB aggregate response ceiling')
   total+=len(raw);row.update(status=r.status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),headers=dict(r.headers),destination=Path(path).name)
   with (OUT/Path(path).name).open('xb')as f:f.write(raw)
 except Exception as e:row.update(error=type(e).__name__+': '+str(e))
 row['wall_seconds']=time.monotonic()-t;records.append(row)
with (OUT/'network-receipt.json').open('x')as f:json.dump({'schema':1,'primary_requests':len(records),'aggregate_body_bytes':total,'limit_bytes':1024**2,'native_engine_execution':False,'responses':records},f,indent=2);f.write('\n')
print(json.dumps({'requests':len(records),'bytes':total,'rows':[{k:v for k,v in r.items()if k in ('source_path','status','bytes','error')}for r in records]}))
