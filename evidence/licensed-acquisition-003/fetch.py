"""Explicit bounded development acquisition; data is never executed or loaded natively."""
import argparse, datetime, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[2]
PLAN=ROOT/'.runs/licensed-expansion-research-003/retrieval-plan.json'
PLAN_SHA='4ab6b6675eeb33b90a1296441f624a5ba3a293c246d65fa021f73d4c6fa79dae'
CAP=10*1024**2
ALLOWED={'pmod-to-qwiic','lipo-disconnector'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def safe(value):
 if not isinstance(value,str)or not value or '\\'in value or '\0'in value:raise ValueError('unsafe relative path')
 p=PurePosixPath(value)
 if p.is_absolute()or any(x in ('','.','..')for x in value.split('/')):raise ValueError('unsafe relative path')
 return Path(*p.parts)
def owned(path):
 if not path.is_relative_to(ROOT)or any(x.is_symlink()for x in (path,*path.parents)):raise ValueError('unsafe local destination')
 return path

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',choices=sorted(ALLOWED),required=True);parser.add_argument('--fetch',action='store_true');args=parser.parse_args()
 raw=PLAN.read_bytes();assert sha(raw)==PLAN_SHA;plan=json.loads(raw);project=next(p for p in plan['projects']if p['slug']==args.project)
 rows=project['proposed_fetch_files'];total=sum(r['bytes']for r in rows);assert total<=CAP and len(rows)<=100
 destinations=set()
 for row in rows:
  dest=safe(row['destination']);source=safe(row['source_path']);assert dest.parts[0]==args.project and dest not in destinations;destinations.add(dest)
  assert row['mode']=='100644'and type(row['bytes'])is int and 0<=row['bytes']<=CAP
  assert row['repository']in ('solderparty/pmod_to_qwiic_adapter','solderparty/lipo_disconnector_hw','arturo182/kicad-modules','arturo182/kicad-library')
  assert re.fullmatch('[0-9a-f]{40}',row['commit'])and re.fullmatch('[0-9a-f]{40}',row['git_blob_sha1'])
  assert row['raw_url']=='https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/'+urllib.parse.quote(row['source_path'],safe='/')
 if not args.fetch:
  print(json.dumps({'action':'plan_only','project':args.project,'files':len(rows),'bytes':total,'development_exposure_before_download':True,'native_or_engine':False}));return
 out=owned(ROOT/'.runs/licensed-acquisition-003'/(args.project+'-001'));base=owned(ROOT/'.data/expansion003');source_root=owned(base/args.project)
 if out.exists()or source_root.exists():raise ValueError('fresh source and receipt directories required; failed/partial acquisitions are preserved')
 out.mkdir();source_root.mkdir(parents=True);started=time.monotonic();received=0
 record={'schema':1,'status':'running','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'split':'development','project':args.project,'source_plan_sha256':PLAN_SHA,'fetcher_sha256':sha(Path(__file__).read_bytes()),'planned_files':len(rows),'planned_bytes':total,'cap_bytes':CAP,'native_executed':False,'engine_executed':False,'dependency_closure':'unqualified pending original reference/notice audit','routing_support':'unqualified','files':[]}
 def save():
  p=out/'receipt.json.partial';p.write_text(json.dumps(record,indent=2)+'\n');os.replace(p,out/'receipt.json')
 save()
 try:
  for row in rows:
   if time.monotonic()-started>300:raise TimeoutError('five minute acquisition ceiling exceeded')
   target=owned(base/safe(row['destination']));target.parent.mkdir(parents=True,exist_ok=True);owned(target)
   request=urllib.request.Request(row['raw_url'],headers={'User-Agent':'KiCad-Autorouter-bounded-development-acquisition/1'})
   with urllib.request.urlopen(request,timeout=min(30.,300-(time.monotonic()-started)))as response:
    if urllib.parse.urlparse(response.url).hostname!='raw.githubusercontent.com':raise ValueError('unexpected redirect')
    data=response.read(row['bytes']+1)
   received+=len(data)
   if received>CAP or len(data)!=row['bytes']:raise ValueError('payload size/cap differs')
   if data.startswith(b'version https://git-lfs.github.com/spec/'):raise ValueError('LFS pointer instead of source')
   blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
   if blob!=row['git_blob_sha1']:raise ValueError('Git blob identity differs')
   digest=sha(data)
   if row.get('sha256')and row['sha256']!=digest:raise ValueError('previous SHA256 identity differs')
   with target.open('xb')as stream:stream.write(data)
   if target.read_bytes()!=data:raise ValueError('written bytes differ')
   record['files'].append({**row,'sha256':digest,'payload_acquired_by_this_research':True,'local_path':str(target.relative_to(ROOT))});record['received_bytes']=received;save()
  expected={r['destination']:r['sha256']for r in record['files']}
  actual={str(p.relative_to(base)):sha(p.read_bytes())for p in source_root.rglob('*')if p.is_file()}
  if actual!=expected:raise ValueError('final complete acquisition inventory differs')
  record.update(status='acquired_unqualified',wall_seconds=time.monotonic()-started,bytes_verified=received);save()
 except BaseException as exc:
  record.update(status='failed',error=type(exc).__name__+': '+str(exc),wall_seconds=time.monotonic()-started,received_bytes=received);save();raise
 print(json.dumps({k:record[k]for k in ('status','project','planned_files','bytes_verified','wall_seconds')}))
if __name__=='__main__':main()
