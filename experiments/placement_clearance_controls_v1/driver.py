"""Fixed two-segment native clearance counterfactual, not routing acceptance.

Two project copies; one60s wall/parent+children CPU budget; no engine. Only an
explicit --run-native launches the lead-scheduled diagnostic. Original rules,
pads/zones and all unselected geometry remain unchanged.
"""
from __future__ import annotations
import argparse,datetime,fcntl,hashlib,json,os,shutil,signal,stat,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(x for x in HERE.parents if (x/'toolchain.lock.json').is_file())
sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(HERE)]
from autorouter import pipeline as p,floor_route as f,sexpr as sx
import recipe as r
import support as s
PAIR=ROOT/'.runs/placement-routing-pair-001';ARM=PAIR/'arm-1'
SOURCE=ROOT/'.data/boards/kicad-multichannel/multichannel_mixer.kicad_pcb'
PAIR_SHA='3a395d1095c345a102028e3b4f7a328c97950f09ee52c6fe0e0f2855f7788ac8'
ARM_SHA='4f2dcec85f8f414c370bf58b6454951012c4ed739b9cf74b775b9a8a13b15f31'
CANDIDATE_SHA='87b82041c0b6fbdbf21cd0ba2b3c08e56195facc984f2a93febc919432ae66e3'
SECONDS=60.;HELPERS=('driver.py','recipe.py','support.py','test_driver.py')
MAX_TREE_BYTES=96*1024**2;MAX_TREE_FILES=2000;MAX_PROJECT_BYTES=5*1024**2;MAX_PROJECT_PAYLOAD_BYTES=20*1024**2

def bounded_tree(path,*,max_bytes=MAX_TREE_BYTES,max_files=MAX_TREE_FILES):
 path=s.owned(path);total=count=0
 if not path.is_dir():raise p.Rejected('bounded tree must be a directory')
 for current,dirs,names in os.walk(path,followlinks=False):
  for name in dirs+names:
   node=Path(current)/name;info=node.lstat()
   if stat.S_ISDIR(info.st_mode):continue
   if not stat.S_ISREG(info.st_mode)or info.st_nlink!=1:raise p.Rejected('linked/special diagnostic input')
   total+=info.st_size;count+=1
   if total>max_bytes or count>max_files:raise p.Rejected('bounded diagnostic tree exceeded')
 return p.tree_hash(path)

def verify_committed(files,head,remaining):
 """Local blob reads only; no native stage may precede the exact commit audit."""
 for relative,digest in files.items():
  path=s.owned(ROOT/relative)
  if str(path.relative_to(ROOT))!=relative or p.sha(path)!=digest:raise p.Rejected('source changed before committed-byte audit')
  timeout=min(5.,remaining())
  if timeout<=0:raise p.Rejected('budget exhausted during committed-byte audit')
  raw=subprocess.run(['git','show',head+':'+relative],cwd=ROOT,capture_output=True,check=True,timeout=timeout).stdout
  if hashlib.sha256(raw).hexdigest()!=digest:raise p.Rejected('commit exact diagnostic/core/toolchain bytes before native execution')
 return dict(files)

def project_size(directory):
 bounded_tree(directory,max_bytes=MAX_PROJECT_BYTES,max_files=18)
 return sum(x.stat().st_size for x in directory.rglob('*')if x.is_file())

def project_payload(out):
 total=0
 for case in r.CASES:
  for name in ('candidate','native-drc-input'):
   path=out/case/name
   if path.exists():total+=project_size(path)
 if total>MAX_PROJECT_PAYLOAD_BYTES:raise p.Rejected('20MiB aggregate project-copy payload exceeded')
 return total

def projected_payload(base_project_bytes,base_board_bytes,encoded_cases):
 # Each candidate has one equal full-project disposable native input copy.
 total=2*sum(base_project_bytes-base_board_bytes+len(raw)for raw in encoded_cases.values())
 if total>MAX_PROJECT_PAYLOAD_BYTES:raise p.Rejected('projected 20MiB project-copy payload exceeded')
 return total

def baseline():
 for path,digest in ((PAIR/'summary.json',PAIR_SHA),(ARM/'result.json',ARM_SHA)):
  if p.sha(s.owned(path))!=digest:raise p.Rejected('pinned prior receipt changed')
 pair=f.read_json(PAIR/'summary.json');prior=f.read_json(ARM/'result.json');protocol=f.read_json(PAIR/'protocol.json')
 if pair.get('status')!='completed'or pair.get('comparison_eligible')is not True or pair['results'][1]['receipt_sha256']!=ARM_SHA:
  raise p.Rejected('prior pair outcome differs')
 if p.sha(PAIR/'protocol.json')!=pair['protocol_sha256']:raise p.Rejected('prior protocol changed')
 for name,hashes in pair['completed_trees'].items():
  if bounded_tree(s.owned(name))!=hashes:raise p.Rejected('recorded prior pair/fixture/source/code tree changed')
 if bounded_tree(ARM)!=pair['completed_trees'][str(ARM)]or f.evidence_inventory(ARM)!=prior['evidence_hashes']:
  raise p.Rejected('prior arm evidence changed')
 candidate=s.owned(ARM/'candidate'/SOURCE.name)
 if (prior['source']!=str(SOURCE)or prior['candidate']!=str(candidate)or prior['candidate_sha256']!=CANDIDATE_SHA
     or p.sha(candidate)!=CANDIDATE_SHA or prior.get('routing_accepted')is not False or prior.get('status')!='drc_rejected'):
  raise p.Rejected('fixed original candidate identity differs')
 source_hashes=bounded_tree(SOURCE.parent,max_bytes=MAX_PROJECT_BYTES,max_files=17)
 if source_hashes!=prior['source_hashes']or source_hashes!=protocol['source_hashes']or bounded_tree(ARM/'snapshot')!=source_hashes:
  raise p.Rejected('complete original source/rules inventory differs')
 expected=dict(source_hashes);expected[SOURCE.name]=CANDIDATE_SHA
 if len(expected)!=17 or bounded_tree(candidate.parent,max_bytes=MAX_PROJECT_BYTES,max_files=17)!=expected:
  raise p.Rejected('original candidate project differs')
 original=p.preflight(SOURCE)
 if p.immutable(sx.read(candidate))!=p.immutable(original):raise p.Rejected('original candidate immutable source geometry differs')
 native=p.parse_report(ARM/'final-drc.json',SOURCE.name)
 if p.sha(ARM/'final-drc.json')!=prior['native_report_sha256']or native!=prior['native']or not r.verdict(r.CASES[0],native,native):
  raise p.Rejected('expected two actual clearance errors/eight opens differ')
 r.prepare(candidate.read_bytes(),r.CASES[1])
 return prior,candidate,source_hashes,expected,pair['completed_trees']

def experiment(out,*,run_native=False):
 if run_native is not True:raise p.Rejected('explicit --run-native required')
 started=time.monotonic();cpu0=s.cpu();out=s.owned(out,exists=False)
 if out.parent!=ROOT/'.runs'or out.exists():raise p.Rejected('fresh direct .runs output required')
 out.mkdir();steps=[];completed={};freeze=None;cases=[]
 record={'schema':1,'kind':'fixed_exposed_two_segment_clearance_counterfactual','status':'running','controls_passed':False,
  'routing_accepted':False,'comparison_eligible':False,'production_qualified':False,'engine_executed':False,
  'geometry_margin_policy_qualified':False,'claims_limit':'Fixed saved-candidate diagnostic only; no general repair, route acceptance, clearance-margin or comparative qualification.',
  'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'predeclared_cases':list(r.CASES),'target_translations_mm':r.TARGETS,'cases':cases,'steps':steps,
  'cost_scope':'All preparation, metadata, copies, native refill/DRC and final publication inside this diagnostic; prior routing acquisition excluded.',
  'accounting_point':'Stored totals precede final publication; actual caps checked again after final readback and freshness.'}
 def remaining():return max(0.,min(started+SECONDS-time.monotonic(),SECONDS-(s.cpu()-cpu0)))
 def account():
  record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=s.cpu()-cpu0,native_executed=bool(steps),
   process_cpu_seconds=sum(x.get('cpu_seconds')or 0 for x in steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds')or 0 for x in steps))
  record['within_budget']=record['wall_seconds']<=SECONDS and record['total_cpu_seconds']<=SECONDS
  if not record['within_budget']:record['controls_passed']=False
 def stable():
  if freeze is None:return
  project_payload(out)
  if bounded_tree(PAIR)!=freeze['prior_pair_tree']or bounded_tree(SOURCE.parent)!=freeze['source_hashes']:
   raise p.Rejected('original full pair/source changed during diagnostic')
  for path,hashes in freeze['prior_recorded_trees'].items():
   if bounded_tree(s.owned(path))!=hashes:raise p.Rejected('prior recorded fixture/source/code changed during diagnostic')
  if p.sha(ROOT/'toolchain.lock.json')!=freeze['toolchain_lock_sha256']:raise p.Rejected('toolchain pin file changed')
  if p.tool_manifest()!=freeze['tools']or any(p.sha(s.owned(HERE/name))!=digest for name,digest in freeze['helpers'].items()):
   raise p.Rejected('current tools/HEAD/core/diagnostic changed')
  if bounded_tree(out/'code')!=freeze['code']:raise p.Rejected('frozen code snapshot changed')
  for name,hashes in completed.items():
   if bounded_tree(s.owned(name))!=hashes:raise p.Rejected('completed diagnostic output changed')
  for entry,job,board in checked:
   if p.sha(board)!=entry['candidate_sha256']or board.read_bytes()!=r.prepare(base_raw,entry['case']):raise p.Rejected('final candidate derivation changed')
   observed=p.parse_report(job.out/'native-drc.json',SOURCE.name)
   if observed!=entry['native']or s.check_drc(job,'native-drc',board,observed)!=entry['native_binding']:raise p.Rejected('final native binding changed')
   if r.verdict(entry['case'],observed,prior['native'])!=entry['passed']:raise p.Rejected('final diagnostic verdict changed')
 checked=[]
 try:
  p.check_storage();prior_pair_tree=bounded_tree(PAIR);prior,candidate,source_hashes,candidate_hashes,prior_trees=baseline();base_raw=candidate.read_bytes()
  tools=p.tool_manifest();lock_sha=p.sha(ROOT/'toolchain.lock.json');helpers={name:p.sha(s.owned(HERE/name))for name in HELPERS}
  committed=dict(tools['implementation_sha256']);committed.update({str((HERE/name).relative_to(ROOT)):digest for name,digest in helpers.items()});committed['toolchain.lock.json']=lock_sha
  verify_committed(committed,tools['git_head'],remaining)
  encoded_cases={case:r.prepare(base_raw,case)for case in r.CASES}
  projected=projected_payload(project_size(candidate.parent),len(base_raw),encoded_cases)
  record.update(project_copy_payload_limit_bytes=MAX_PROJECT_PAYLOAD_BYTES,projected_project_copy_payload_bytes=projected)
  (out/'code').mkdir()
  for name in HELPERS:
   shutil.copy2(HERE/name,out/'code'/name)
   if p.sha(out/'code'/name)!=helpers[name]:raise p.Rejected('helper changed during snapshot')
  for relative,digest in tools['implementation_sha256'].items():
   source=s.owned(ROOT/relative);dest=out/'code'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
   if p.sha(dest)!=digest:raise p.Rejected('core changed during code snapshot')
  shutil.copy2(ROOT/'toolchain.lock.json',out/'code/toolchain.lock.json')
  if p.sha(out/'code/toolchain.lock.json')!=lock_sha:raise p.Rejected('toolchain lock changed during snapshot')
  freeze={'committed_source_bytes':committed,'prior_recorded_trees':prior_trees,'toolchain_lock_sha256':lock_sha,'tools':tools,'helpers':helpers,'code':bounded_tree(out/'code'),'source_hashes':source_hashes,'prior_pair_tree':prior_pair_tree}
  record.update(freeze=freeze,prior_pair_summary_sha256=PAIR_SHA,prior_arm_receipt_sha256=ARM_SHA,prior_candidate_sha256=CANDIDATE_SHA,
   source=str(SOURCE),source_hashes=source_hashes,prior_native=prior['native'])
  for case in r.CASES:
   stable()
   if remaining()<5:raise p.Rejected('shared diagnostic reserve exhausted')
   job=s.SharedJob(out/case,remaining,steps);board=job.out/'candidate'/SOURCE.name;shutil.copytree(candidate.parent,board.parent)
   encoded=encoded_cases[case];board.write_bytes(encoded);hashes=dict(candidate_hashes);hashes[SOURCE.name]=p.sha(board)
   if bounded_tree(board.parent,max_bytes=MAX_PROJECT_BYTES,max_files=17)!=hashes:raise p.Rejected('derived copy changed unrelated project files')
   entry={'case':case,'passed':False,'routing_accepted':False,'candidate':str(board),'candidate_sha256':p.sha(board),'project_hashes':hashes,
    'only_declared_endpoints_changed':True,'native':None,'steps':job.steps};cases.append(entry)
   if project_payload(out)+project_size(board.parent)>MAX_PROJECT_PAYLOAD_BYTES:raise p.Rejected('next native copy exceeds aggregate payload budget')
   native=job.drc('native-drc',board);record['actual_project_copy_payload_bytes']=project_payload(out);binding=s.check_drc(job,'native-drc',board,native)
   if bounded_tree(board.parent,max_bytes=MAX_PROJECT_BYTES,max_files=17)!=hashes:raise p.Rejected('native modified derived candidate/rules')
   entry.update(native=native,native_binding=binding,passed=r.verdict(case,native,prior['native']),native_accepted=p.native_accepted(native),
    source_project_unchanged=True,actual_minimum_clearance_mm=.3,finished_wall_seconds=time.monotonic()-started,finished_cpu_seconds=s.cpu()-cpu0)
   p.save_json(job.out/'case.json',entry);completed[str(job.out)]=bounded_tree(job.out);checked.append((entry,job,board))
  stable();record.update(status='completed',controls_passed=len(cases)==2 and all(row['passed']for row in cases),original_pair_and_source_unchanged=True,completed_evidence=completed)
 except (Exception,KeyboardInterrupt)as exc:
  record.update(status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
 return s.publish(out,record,stable,account)

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--run-native',action='store_true');args=parser.parse_args(argv)
 if not args.run_native:parser.error('--run-native required; no native work executed')
 previous={sig:signal.getsignal(sig)for sig in (signal.SIGINT,signal.SIGTERM)}
 def interrupted(*_):raise KeyboardInterrupt
 try:
  for sig in previous:signal.signal(sig,interrupted)
  lock=s.owned(ROOT/'.runs/quality-experiment.lock',exists=False)
  with lock.open('a')as stream:
   fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);value=experiment(args.output,run_native=True)
  print(json.dumps({'status':value['status'],'controls_passed':value['controls_passed'],'routing_accepted':False,'output':str(args.output)}))
  return 0 if value['controls_passed']else 1
 finally:
  for sig,handler in previous.items():signal.signal(sig,handler)
if __name__=='__main__':raise SystemExit(main())
