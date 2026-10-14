"""Focused current selector/fetch publication controls; authored payloads only."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys,time
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from scripts import fetch_led_demo as demo,experiment_quality as q
rows=copy.deepcopy(demo.ROWS);payloads={}
for row in rows:
 raw=('authored current selector '+row['source_path']+'\n').encode();payloads[row['source_path']]=raw
 row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),git_blob_sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
def prepare(name):
 root=HERE/name;project=root/'.data/led-demo-001/project';project.mkdir(parents=True)
 for filename,raw in payloads.items():(project/filename).write_bytes(raw)
 return root,project
def forbidden(*args,**kwargs):raise AssertionError('No subprocess/Git/native/network in pure controls')
results={}
# Same forbidden staging/replacement owner population as the demonstrated gap.
root,project=prepare('current-selector');replacement=root/'.runs/led-demo-benchmark-source';replacement.mkdir(parents=True);(replacement/'PushButtonLed.kicad_pcb').write_bytes(b'owner');identity=(replacement.stat().st_dev,replacement.stat().st_ino)
with patch.object(demo,'ROWS',tuple(rows)),patch.object(q.c,'ROOT',root),patch.object(Path,'write_bytes',forbidden),patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
 board,family=q.selected_source('push-button-led')
 assert board==project/'PushButtonLed.kicad_pcb'
assert (replacement/'PushButtonLed.kicad_pcb').read_bytes()==b'owner' and (replacement.stat().st_dev,replacement.stat().st_ino)==identity
results['read_only_selection_preserves_existing_staging_owner']=True
root,project=prepare('current-stale');real_read=Path.read_bytes;mutated=[]
def mutate_during_capture(path):
 raw=real_read(path)
 if path==project/'PushButtonLed.kicad_pcb' and not mutated:
  # The first inventory reads this file; mutation is deliberately after it.
  mutated.append(True);(project/'README.md').write_bytes(b'owner changed original source')
 return raw
with patch.object(demo,'ROWS',tuple(rows)),patch.object(q.c,'ROOT',root),patch.object(Path,'read_bytes',mutate_during_capture):
 try:q.selected_source('push-button-led')
 except (q.p.Rejected,ValueError) as exc:results['stale_capture_rejected']=type(exc).__name__+': '+str(exc)
 else:raise AssertionError('changed source selected')
assert not (root/'.runs').exists()
root,project=prepare('canonical-corrupt');canonical=root/'.runs/push-button-led-original-native-001/original';canonical.mkdir(parents=True);(canonical/'owner').write_bytes(b'owner')
with patch.object(demo,'ROWS',tuple(rows)),patch.object(q.c,'ROOT',root):
 try:q.selected_source('push-button-led')
 except (ValueError,FileNotFoundError,q.p.Rejected) as exc:results['corrupt_canonical_not_silently_replaced']=type(exc).__name__+': '+str(exc)
 else:raise AssertionError('corrupt canonical silently fell back')
assert (canonical/'owner').read_bytes()==b'owner'
# New post-write OSError plus failed corrective writes must archive any success.
root=HERE/'corrective-write-failure';root.mkdir()
for name in demo.MATERIAL:
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
calls=[]
def transport(row,record,path,allowance,remaining):
 remaining();raw=payloads[row['source_path']]
 with path.open('xb') as f:f.write(raw)
 record.update(received_bytes=len(raw),response_sha256=demo.shared.sha(raw),url=row['raw_url'],status='response_received',http_status=200,wall_seconds=0.)
 return raw
save=demo.publication.p.save_json
def failed_publication(path,record):
 calls.append(path)
 if len(calls)==1:save(path,record)
 raise OSError('controlled first post-write/corrective-write failure')
with patch.object(demo,'ROWS',tuple(rows)),patch.object(demo.publication.p,'save_json',failed_publication),patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
 try:demo.fetch_demo('.data/led-demo-test',fetch=True,root=root,transport=transport)
 except Exception as exc:results['corrective_write_failure']=type(exc).__name__+': '+str(exc)
 else:raise AssertionError('failed final publication returned success')
out=root/'.data/led-demo-test';archives=list(out.glob('invalidated-result-*.json'))
assert not (out/'result.json').exists() and archives and all(demo.publication.read_json(p)['accepted'] is False for p in archives)
results['no_canonical_source_success_after_failed_corrections']=True
# Literal public identities remain exact against the versioned source profile.
public=json.loads((ROOT/'experiments/licensed_acquisition_v7/protocol.json').read_text())['projects'][0]['files'];keys=['source_path','repository','commit','mode','raw_url','bytes','sha256','git_blob_sha1']
assert [{k:r[k] for k in keys} for r in demo.ROWS]==[{k:r[k] for k in keys} for r in public]
results['fixed_five_public_source_identities_equal_v7']=True
results['code_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['scripts/fetch_led_demo.py','scripts/experiment_quality.py','tests/test_led_demo_fetch.py','tests/test_demo_benchmark_source.py','experiments/licensed_acquisition_v1/fetch.py']}
print(json.dumps({'schema':1,'scope':'Pure authored fixtures/API seams only; no native/HTTP/Git subprocess. Old selector reproduction retained.','results':results},indent=2))
