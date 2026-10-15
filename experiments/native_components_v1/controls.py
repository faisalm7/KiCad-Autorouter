"""Real sequential API controls using shared Native, process and publication checks."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,hashlib,json,shutil,signal,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,config as c,handoff as h,placement_clearance as pc
from experiments.native_components_v1 import fixtures
SECONDS=180
WRAPPER='cd1c06c4709c653256ebd0c98c66d80cd72033767fac27c34ea01b5ec586116a'
class OfflineJob(p.Job):
 def step(self,name,argv,allowed=(0,)):return super().step(name,[*f.SANDBOX,*argv],allowed)
def account_delivery(record,wall,full):
 record.update(wall_seconds=wall,full_cpu_seconds=full)
 if max(wall,full)+2>SECONDS:record.update(passed=False,status='budget_exceeded')
 if record.get('status')!='completed':record['passed']=False
def completed_inventory(folder):return pc.inventory(folder,max_bytes=16*1024**2,max_files=256,max_entries=512,with_directories=True)
def check_completed(completed):
 for folder,expected in completed.items():
  if completed_inventory(folder)!=expected:raise p.Rejected('completed component control changed')
def intended_short_observed(native):
 intended={fixtures.uid(label).strip('"') for label in ('short','B')}
 return native['blocking']>0 and p.native_accepted(native) is False and any(
  finding.get('type') in {'shorting_items','tracks_crossing','clearance'}
  and finding.get('severity')=='error' and not finding.get('excluded',False)
  and intended.issubset({item.get('uuid') for item in finding.get('items',[])})
  for finding in native['findings'])
def run(output):
 output=Path(output).absolute();assert output.parent==ROOT/'.runs' and output==output.resolve() and not output.exists()
 output.mkdir();owner={};h.capture_destination(owner,output);tools=p.tool_manifest()
 own={str(q.relative_to(ROOT)):p.sha(q) for q in Path(__file__).parent.glob('*.py')}
 own.update({n:p.sha(ROOT/n) for n in ('fixtures/smoke/smoke.kicad_pcb','fixtures/smoke/smoke.kicad_pro','toolchain.lock.json')})
 for n,pin in own.items():assert hashlib.sha256(subprocess.check_output(['git','show',tools['git_head']+':'+n],cwd=ROOT)).hexdigest()==pin
 wrapper=c.PCBNEW.with_name('pcbnew.py');assert p.sha(wrapper)==WRAPPER
 record=dict(schema=1,kind='actual-native-pad-component-controls-v1',status='incomplete',passed=False,accepted=False,routing_accepted=False,production_admitted=False,tools=tools,source_sha256=own,pcbnew_wrapper_sha256=WRAPPER,controls=[],budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,schematic_parity='unavailable on owned PCB-only API fixtures',scope='Actual saved refill, original-shell final Native and full pad partitions. No routing/engine execution or support admission. Every deliberate invalid source remains invalid.')
 def elapsed():return time.monotonic()-START,cpu()-CPU0
 def remaining():return SECONDS-max(elapsed())
 material=None;completed={}
 def stable():
  h.owned_destination(owner);assert remaining()>0 and p.tool_manifest()==tools and p.sha(wrapper)==WRAPPER
  assert all(p.sha(ROOT/n)==pin for n,pin in own.items())
  check_completed(completed)
  if material is not None:assert f.evidence_inventory(output)==material
 def account():
  account_delivery(record,*elapsed())
 try:
  stable();base=sx.read(ROOT/'fixtures/smoke/smoke.kicad_pcb')
  for case in fixtures.CASES:
   stable();job=OfflineJob(output/case,min(35,remaining()-4),protect_local_settings=True)
   entry=dict(case=case,passed=False);record['controls'].append(entry)
   try:
    original,expected=fixtures.recipe(case,base);source=job.out/'original';source.mkdir();board=source/'smoke.kicad_pcb';sx.write(board,original);shutil.copyfile(ROOT/'fixtures/smoke/smoke.kicad_pro',board.with_suffix('.kicad_pro'));hashes=p.tree_hash(source)
    saved=job.out/'saved'/board.name;shutil.copytree(source,saved.parent)
    native=job.drc('refill-drc',saved,save=True)
    assert f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',saved,saved,True,hashes)==native
    candidate=job.out/'candidate'/board.name;shutil.copytree(source,candidate.parent);sx.write(candidate,p.transplant_fill(original,sx.read(saved)))
    assert p.immutable(sx.read(candidate))==p.immutable(original) and p.routes(sx.read(candidate))==p.routes(original)
    before=p.tree_hash(candidate.parent);final=job.drc('final-drc',candidate)
    assert f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,job.out/'final-drc-input'/candidate.name,False,before)==final
    if case=='physical-short':assert intended_short_observed(final)
    else:assert final['blocking']==0 and final['opens']==(1 if case in ('chain-cut','zone-islands','layer-gap') else 0)
    request=job.out/'request.json';spec=dict(schema=1,board=str(candidate),project_sha256=p.tree_hash(candidate.parent),refill_receipt=str(job.out/'refill-drc-binding.json'),refill_receipt_sha256=p.sha(job.out/'refill-drc-binding.json'),worker_sha256=own['experiments/native_components_v1/worker.py'],normalizer_sha256=own['experiments/native_components_v1/normalize.py'],lock_sha256=own['toolchain.lock.json'],wrapper_sha256=WRAPPER);p.save_json(request,spec)
    hintout=job.out/'components';job.step('components',[str(c.PYTHON),str(ROOT/'experiments/native_components_v1/worker.py'),'--request',str(request),'--output',str(hintout)])
    f.process_check(job.out,{'steps':job.steps},'components',[*f.SANDBOX,str(c.PYTHON),str(ROOT/'experiments/native_components_v1/worker.py'),'--request',str(request),'--output',str(hintout)])
    hint=f.read_json(hintout/'result.json');assert hint['status']=='diagnostic_completed' and all(hint[k] is False for k in ('accepted','routing_accepted','production_admitted','board_saved','native_refill_performed','refill_semantics_checked_by_worker'))
    assert hint['source_hashes']==before and hint['request_sha256']==p.sha(request) and hint['tools'][str(wrapper)]==WRAPPER
    refs={row['uuid']:row['reference'] for row in hint['pad_census']};observed=sorted(sorted(refs[u] for u in group['pad_uuids']) for group in hint['components']);assert observed==expected
    assert p.tree_hash(source)==hashes and p.tree_hash(candidate.parent)==before and p.sha(candidate)==before[candidate.name]
    entry.update(passed=True,native_counts={k:final[k] for k in ('opens','blocking','warnings','exclusions')},expected_components=expected,observed_components=observed,pad_count=len(refs),component_receipt_sha256=p.sha(hintout/'result.json'),candidate_sha256=p.sha(candidate),native_report_sha256=p.sha(job.out/'final-drc.json'),steps=job.steps)
    completed[job.out]=completed_inventory(job.out)
   except BaseException:
    entry['steps']=job.steps;raise
  record.update(status='completed',passed=True)
 except BaseException as ex:record.update(status='failed',passed=False,reason=type(ex).__name__+': '+str(ex))
 account();material=f.evidence_inventory(output);record['completed_material']=material
 f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 print(json.dumps({k:record.get(k) for k in ('status','passed','reason','wall_seconds','full_cpu_seconds')}));return record
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-native',action='store_true');ap.add_argument('--output',required=True);args=ap.parse_args()
 if not args.run_native:ap.error('explicit --run-native required')
 def stop(*_):raise KeyboardInterrupt
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
 result=run(args.output);raise SystemExit(0 if result['status']=='completed' and result['passed'] is True else 2)
