"""Actual saved-evidence handoff compatibility; no native/engine/GUI/network."""
from pathlib import Path
import hashlib,json,resource,sys,time,traceback
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import handoff as h, pipeline as p, placement_clearance as pc, floor_route as f
EXPECTED='74f022bae8a8d89ebf86d7d2a3255a7c41a6f171e041ecc0c73ee5346a82a936'
CASES={'historical-C':ROOT/'.runs/quality-comparison-001/C/result.json','thermal-C':ROOT/'.runs/thermal-paired-001/C_thermal/result.json'}
def cpu():
 a=resource.getrusage(resource.RUSAGE_SELF);b=resource.getrusage(resource.RUSAGE_CHILDREN)
 return a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime

def inventory(folder,evidence=False):
 return pc.inventory(folder,max_bytes=(100 if evidence else 32)*1024**2,max_files=4000 if evidence else 2000,max_entries=8000 if evidence else 4000)

def snapshot(receipt):
 data=f.read_json(receipt);source=Path(data['source']).parent
 return {'source':inventory(source),'run':inventory(receipt.parent,True),'candidate':inventory(Path(data['candidate']).parent)}

def case(name,receipt):
 start=time.monotonic();start_cpu=cpu();row={'name':name,'receipt':str(receipt),'native_execution':False,'engine_execution':False,'gui_execution':False,'network_execution':False,'passed':False}
 before=None
 try:
  before=snapshot(receipt);p.save_json(HERE/(name+'-before.json'),before)
  row['source_files']=len(before['source']);row['run_files']=len(before['run']);row['candidate_files']=len(before['candidate'])
  row['before_check_result']=p.check_result(receipt)
  if row['before_check_result'].get('input_policy','native')!='native':raise AssertionError('not native policy')
  handoff_start=time.monotonic();handoff_cpu=cpu()
  row['review']=h.review_copy(receipt,HERE/name)
  row['handoff_outer_wall_seconds']=time.monotonic()-handoff_start;row['handoff_outer_cpu_seconds']=cpu()-handoff_cpu
  row['after_check_result']=p.check_result(receipt)
  after=snapshot(receipt);p.save_json(HERE/(name+'-after.json'),after)
  copied=inventory(HERE/name/'project');row['copied_project_hashes']=copied
  record=f.read_json(HERE/name/'review.json')
  row['canonical_matches_return']=f.canonical(record)==f.canonical(row['review'])
  row['originals_unchanged']=before==after
  row['copied_project_equal']=copied==before['candidate']==row['review']['initial_project_hashes']
  row['same_candidate']=row['before_check_result']==row['after_check_result']
  row['passed']=all(row[k] for k in ('canonical_matches_return','originals_unchanged','copied_project_equal','same_candidate')) and record['status']=='ready_for_manual_review' and record['input_policy']=='native' and record['source_receipt_schema']==1 and record['native_validation_performed'] is False and record['within_budget'] is True
  if not row['passed']:raise AssertionError('compatibility checks differ')
 except BaseException as exc:
  row['passed']=False;row['error']=type(exc).__name__+': '+str(exc);row['traceback']=traceback.format_exc()
  if before is not None:
   try:
    after=snapshot(receipt);p.save_json(HERE/(name+'-after-failure.json'),after);row['originals_unchanged']=before==after
   except Exception as failure:row['after_failure_error']=str(failure)
 finally:
  row['command_wall_seconds']=time.monotonic()-start;row['command_full_cpu_seconds']=cpu()-start_cpu
  p.save_json(HERE/(name+'-audit.json'),row)
 return row

def main():
 started=time.monotonic();cpu0=cpu();runtime=h.runtime_inventory()
 assert hashlib.sha256(pc.read_bytes(Path(h.__file__))).hexdigest()==EXPECTED
 rows=[]
 for name,receipt in CASES.items():
  if time.monotonic()-started>60 or cpu()-cpu0>60:raise RuntimeError('shared compatibility audit budget exhausted')
  rows.append(case(name,receipt))
 elapsed=time.monotonic()-started;used=cpu()-cpu0;unchanged=h.runtime_inventory()==runtime
 result={'schema':1,'passed':all(row['passed'] for row in rows) and unchanged and elapsed<=60 and used<=60,
         'handoff_source_sha256':EXPECTED,'runtime_source_unchanged':unchanged,'runtime_source_hashes':runtime,
         'wall_seconds':elapsed,'total_cpu_seconds':used,'budget_seconds':60,'cpu_budget_seconds':60,
         'accounting_point':'Stored full-command timings sampled after both copies/readbacks/inventories and before final report publication; each handoff separately checks its own30-second postpublication caps.',
         'cases':[{'name':row['name'],'passed':row['passed'],'files':row.get('run_files'),'wall_seconds':row['command_wall_seconds'],'cpu_seconds':row['command_full_cpu_seconds']} for row in rows],
         'native_execution':False,'engine_execution':False,'gui_execution':False,'network_execution':False,'scope':'Saved-evidence consistency and complete disposable filesystem copies under modified local core. No fresh native validation, GUI qualification or live application.'}
 p.save_json(HERE/'summary.json',result)
 print(json.dumps({key:result[key] for key in ('passed','cases','wall_seconds','total_cpu_seconds','runtime_source_unchanged')},indent=2))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
