"""Finite actual native controls using shared handoff/process controls; no routing."""
from pathlib import Path
import hashlib,json,os,signal,sys,time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import handoff as h, floor_route as f, pipeline as p, runner
mode=sys.argv[1];assert mode in ('tamper','cancel')
output=ROOT/'.runs'/('review-render-'+mode+'-001')
receipt=ROOT/'.runs/default-tuning-native-001/result.json'
report=json.loads(receipt.read_bytes());source=Path(report['source']).parent
before_source=h.pc.inventory(source);before_run=h.pc.inventory(receipt.parent,max_bytes=h.EVIDENCE_BYTES,max_files=4000,max_entries=8000)
observed=[];caught=None
step=f.FloorJob.step;rss=runner._group_rss_bytes

def tamper(job,name,argv,*args,**kwargs):
 result=step(job,name,argv,*args,**kwargs)
 observed.append({'stage':name,'status':result['status'],'exit_code':result['exit_code']})
 if len(observed)==2:
  target=job.out/'plots/before-F.Cu.svg';raw=target.read_bytes()
  preserved=ROOT/'.runs/review-render-tamper-001-first-display-original.svg';preserved.write_bytes(raw)
  target.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
  observed.append({'target':str(target),'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':p.sha(target),'preserved':str(preserved)})
 return result

def cancel(pgid,cwd):
 result=rss(pgid,cwd)
 if not observed:
  os.killpg(pgid,0)
  observed.append({'live_native_group':pgid,'signal_target':os.getpid(),'signal':'SIGTERM','at_monotonic':time.monotonic()})
  os.kill(os.getpid(),signal.SIGTERM)
 return result

with (patch.object(f.FloorJob,'step',tamper) if mode=='tamper' else patch.object(runner,'_group_rss_bytes',cancel)):
 try:h.review_copy(receipt,output,render=True)
 except Exception as exc:caught=type(exc).__name__+': '+str(exc)
record=json.loads((output/'review.json').read_bytes())
assert caught and record['status'] in ('rejected','cancelled') and not (output/'preview.html').exists()
assert h.pc.inventory(source)==before_source
assert h.pc.inventory(receipt.parent,max_bytes=h.EVIDENCE_BYTES,max_files=4000,max_entries=8000)==before_run
processes=[json.loads(x.read_bytes()) for x in sorted((output/'plot-work').glob('*-process.json'))]
if mode=='tamper':
 assert 'completed preview stage changed' in caught
 assert len(processes)==2 and all(x['status']=='success' for x in processes)
else:
 assert len(processes)==1 and processes[0]['status']=='cancelled' and processes[0]['cancel_signal']=='SIGTERM'
 try:os.killpg(observed[0]['live_native_group'],0)
 except ProcessLookupError:pass
 else:raise AssertionError('native group still exists')
value={'schema':1,'mode':mode,'passed':True,'observed':observed,'error':caught,'status':record['status'],'source_and_routing_evidence_unchanged':True,'no_ready_html':True,'native_processes':processes,'source_sha256':{name:p.sha(ROOT/name) for name in ('autorouter/review_view.py','autorouter/handoff.py','autorouter/runner.py')},'control_sha256':p.sha(Path(__file__)),'scope':'Actual native plot stages, intentional post-stage display mutation or real supervisor SIGTERM. No new routing/DRC/GUI claim.'}
target=ROOT/'.runs'/('review-render-'+mode+'-001-control.json');assert not target.exists();target.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
