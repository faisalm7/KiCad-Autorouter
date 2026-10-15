"""One bounded enclosure for the missing-only HFE netlist probe; no admission."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,json,sys,signal
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,local_settings as ls,schematic_field_evidence as field_evidence
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as original
OUT=ROOT/'.runs/hfe-parity-probe-execution-001';CHILD=OUT/'probe';CONTROLLER=ROOT/'.runs/run-hfe-parity-probe-001.py'
CAP=90;PUBLICATION=2

def main(head):
 original.clean(head)
 controller_pin=p.sha(CONTROLLER);outer_pin=p.sha(Path(__file__))
 # Explicit caller record is checked against the same signed proof as the
 # original diagnostic; the child independently declares literal tool hashes.
 proof=f.read_json(original.PROOF)
 if p.sha(original.PROOF)!=original.PROOF_PIN:raise p.Rejected('signed proof changed')
 nt=p.ExperimentalNativeToolchain.from_record(proof['experimental_native_toolchain']);tools=p.tool_manifest(native_toolchain=nt)
 OUT.mkdir();owner={};h.capture_destination(owner,OUT)
 def remaining():return min(CAP-PUBLICATION-(time.monotonic()-START),CAP-PUBLICATION-(cpu()-CPU0))
 argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(CONTROLLER),'--source-head',head,'--controller-sha256',controller_pin,'--output',str(CHILD)]
 # CHILD owns the existing quality lock. Parent must not acquire it twice.
 process=run(argv,cwd=OUT,log=OUT/'command.log',timeout=max(.001,min(60,remaining())),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=2*1024**3)
 path=CHILD/'result.json';child=f.read_json(path) if path.is_file() else None
 child_pin=p.sha(path) if child is not None else None;literal=f.canonical(child) if child is not None else None
 bound=bool(child and original.material(CHILD)==child.get('completed_evidence') and p.sha(path)==child_pin and f.canonical(f.read_json(path))==literal)
 witness=original.material(OUT);log_pin=p.sha(OUT/'command.log')
 passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('observation_complete') is True and child.get('accepted') is False and child.get('production_support_qualified') is False and child.get('tools')==tools and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
 record=dict(schema=1,accepted=False,passed=passed,status='cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'completed' if passed else 'failed',production_support_qualified=False,git_head=head,tools=tools,process=process,controller_sha256=controller_pin,enclosure_sha256=outer_pin,child_receipt_sha256=child_pin,child_completed_evidence_bound=bound,completed_evidence=witness,child=child,log_sha256=log_pin,limits=dict(whole_wall_full_cpu_seconds=CAP,child_wall_full_cpu_seconds=60,scratch_bytes=128*1024**2,group_rss_bytes=2*1024**3,log_bytes=256*1024,publication_allowance_seconds=PUBLICATION),scope='One missing-only originalHFE schematic export/terminal diagnostic. Passed means actual export and parse completed; rename-only hypothesis remains a separate result. No DRC repeat/engine/routing/repair/waiver/support admission.')
 def fresh():
  h.owned_destination(owner);original.clean(head);original.source()
  if (p.tool_manifest(native_toolchain=nt)!=tools or p.sha(original.PROOF)!=original.PROOF_PIN or p.sha(CONTROLLER)!=controller_pin or p.sha(Path(__file__))!=outer_pin or original.material(OUT)!=witness or p.sha(OUT/'command.log')!=log_pin):raise p.Rejected('enclosing source/tool/material changed')
  if child is not None and (not bound or original.material(CHILD)!=child['completed_evidence'] or p.sha(path)!=child_pin or f.canonical(f.read_json(path))!=literal):raise p.Rejected('child literal/prepublication witness changed')
  if child and child.get('observation_complete'):
   plan=f.read_json(CHILD/'protocol.json');job=CHILD/'job';board=job/'input'/(original.STEM+'.kicad_pcb')
   name=field_evidence.names('parity-probe')[0]
   expected=field_evidence.arguments(job,'parity-probe',board,native_toolchain=nt)[0]
   proc=f.process_check(job,child,name,[*f.SANDBOX,*expected])
   ls.check_preserved(board.with_suffix('.kicad_prl'),plan['input_with_owned_prl_sha256'],proc['local_settings_protection'])
  if remaining()<=0:raise p.Rejected('whole diagnostic budget exhausted')
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=PUBLICATION)
  if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
  if record['status']!='completed':record['passed']=False
 f.publish(OUT,record,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=fresh)
 row=f.read_json(OUT/'result.json');print(f.canonical({k:row.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds')}))
 return 0 if row.get('passed') is True and row.get('status')=='completed' else 2

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-head',required=True);args=parser.parse_args()
 def interrupted(*_):raise KeyboardInterrupt
 for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
 raise SystemExit(main(args.source_head))
