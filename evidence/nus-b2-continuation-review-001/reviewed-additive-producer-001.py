"""Fresh additive readback; preserves every original and completed native stage."""
from pathlib import Path
import time,sys
START=time.monotonic();CPU0=time.process_time()
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import copy,datetime,json,signal
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h,sexpr as sx
from scripts import experiment_portfolio as m,experiment_paired as paired,experiment_quality as q
CPU0+=f.child_cpu()
CAP=25.0
out=ROOT/'.runs/nus-additive-comparison-001';out.mkdir();owner={};h.capture_destination(owner,out)
old=ROOT/'.runs/nus-native-paired-002';new=ROOT/'.runs/nus-b2-portfolio-continuation-001'
paths=[old,new,ROOT/'.runs/portfolio-resume-draft-001/resume-plan.json',ROOT/'.runs/nus-b2-portfolio-continuation-001-protocol.json']
inputs={str(x):pc.inventory(x,with_directories=True) if x.is_dir() else p.sha(x) for x in paths}
protocol=f.read_json(new/'portfolio/protocol.json');summary=f.read_json(new/'portfolio/portfolio-summary.json');base=f.read_json(old/'run/paired-summary.json');oldouter=f.read_json(old/'execution.json');newouter=f.read_json(new/'execution.json')
board=Path(protocol['source']);original=p.preflight(board);rows=[]
report={'schema':1,'kind':'additive-resumed-development-comparison-v1','status':'incomplete','accepted':False,'comparison_eligible':False,'physical_electrical_validation':False,'controller_sha256':p.sha(Path(__file__)),'protocol_sha256':p.sha(new/'portfolio/protocol.json'),'original_pair_sha256':p.sha(old/'run/paired-summary.json'),'new_portfolio_sha256':p.sha(new/'portfolio/portfolio-summary.json'),'inputs':inputs,'audit_wall_and_cpu_charge_seconds':CAP,'audit_charge_policy':'Charge the complete fixed25second wall and fullCPU final-audit/emission allowance to EACH arm; actual complete audit must fit this bound, including imports, readback and publication. This is a conservative upper charge, not measured algorithm duration.','calendar_gap':newouter['calendar_gap'],'original_failed_receipts_unchanged':True,'new_native_execution':False,'default_trial_repeated':False,'claims_limit':'One exposed development board; no proven independent pedigree, broad completion, heldout, continuous elapsed120second, electrical or physical claim.'}
def remaining():return min(CAP-(time.monotonic()-START),CAP-(time.process_time()+f.child_cpu()-CPU0))
def stable():
 try:
  q.verify_freeze(protocol['freeze'],board);m.verify_resume_basis(protocol['resume'])
  for x in paths:
   current=pc.inventory(x,with_directories=True) if x.is_dir() else p.sha(x)
   if current!=inputs[str(x)]:raise p.Rejected('retained input changed')
  if report['comparison_eligible'] and remaining()<=0:raise p.Rejected('complete additive readback exceeded charged allowance')
 except BaseException:
  report.update(comparison_eligible=False,comparisons=[]);raise

def raw_check(path,expected):
 d=f.read_json(path);folder=path.parent;candidate=Path(d['candidate'])
 assert p.sha(path)==expected['result_sha256'] and d['source']==str(board) and d['source_hashes']==protocol['freeze']['source_hashes']
 assert p.tree_hash(folder/'snapshot')==d['source_hashes']
 p.verify_candidate_files(candidate,d['source_hashes'],d['candidate_sha256'])
 assert p.immutable(sx.read(candidate))==p.immutable(original)
 protected=p.protected_for_record(d,original)
 assert all(x in p.routes(sx.read(candidate)) for x in protected)
 p.check_protected_import(folder,d,original,candidate,protected)
 before=dict(d['source_hashes']);before[candidate.name]=d['candidate_sha256']
 native=f.check_drc_stage(folder,d,'final-drc',candidate,folder/'final-drc-input'/candidate.name,False,before,schematic_parity=True,sandboxed=False)
 assert native==d['native'] and p.sha(folder/'final-drc.json')==d['native_report_sha256']
 p.check_pour_evidence(folder,d,original,candidate)
 metrics=f.read_json(folder/'metrics.json');assert metrics==d['metrics']
 f.process_check(folder,d,'metrics',[str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'metrics',str(candidate),str(folder/'metrics.json')])
 p.check_resource_accounting(d)
 assert d['accepted'] is False and d['status']=='drc_rejected' and p.native_rejection_reasons(native)
 return {'result':str(path),'result_sha256':p.sha(path),'candidate_sha256':d['candidate_sha256'],'native_report_sha256':d['native_report_sha256'],'metrics':metrics,'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'reasons':p.native_rejection_reasons(native),'original_design_and_native_checks':True}

def account():
 report.update(observed_audit_wall_seconds=time.monotonic()-START,observed_audit_full_cpu_seconds=time.process_time()+f.child_cpu()-CPU0)
 eligible=report['status']=='completed' and remaining()>0
 for row in rows:
  row['charged_wall_seconds']=row['whole_invocation_wall_seconds']+base['shared_overhead_wall_seconds']+max(0,oldouter['wall_seconds']-base['batch_wall_seconds'])+CAP
  row['charged_full_cpu_seconds']=row['whole_invocation_full_cpu_seconds']+base['shared_overhead_cpu_seconds']+max(0,oldouter['full_cpu_seconds']-base['batch_cpu_seconds'])+CAP
  row['within_equal120_wall_full_cpu_caps']=max(row['charged_wall_seconds'],row['charged_full_cpu_seconds'])<=120
  row['accepted']=row['native_accepted'] and row['within_equal120_wall_full_cpu_caps'] and eligible
 report.update(comparison_eligible=eligible and all(r['within_equal120_wall_full_cpu_caps'] for r in rows),results=rows,comparisons=paired.comparisons(rows) if eligible else [])
 if remaining()<=0:report.update(status='budget_exceeded',comparison_eligible=False,comparisons=[])

def interrupted(signum,frame):raise KeyboardInterrupt
previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGINT,signal.SIGTERM)}
try:
 stable();assert summary['status']=='completed' and summary['comparison_eligible'] is True and summary['protocol_sha256']==p.sha(new/'portfolio/protocol.json')
 assert [r['id'] for r in summary['trials']]==list(m.VARIANTS)
 eligible=[];negative=[]
 for row in summary['trials']:
  if row['eligible']:
   m.verify_row(row,board,m.trial_freeze(protocol,row));eligible.append(row)
  else:negative.append(raw_check(Path(row['result']),row))
 chosen=min(eligible,key=m.rank)
 assert summary['pareto_frontier']==m.frontier(summary['trials']) and all(summary['selected'][k]==chosen[k] for k in ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm'))
 assert newouter['process']['status']=='success' and newouter['process']['exit_code']==0 and newouter['process']['cleanup_complete'] and newouter['within_enclosing_budget']
 assert newouter['combined_active_wall_seconds']==protocol['resume']['prior_wall_seconds']+newouter['whole_new_wall_seconds']
 assert newouter['combined_full_cpu_seconds']==protocol['resume']['prior_cpu_seconds']+newouter['whole_new_full_cpu_seconds']
 for oldrow in base['results']:
  if oldrow['id']=='B2_portfolio':continue
  row={k:copy.deepcopy(oldrow[k]) for k in ('id','status','result','result_sha256','candidate_sha256','native_report_sha256','length_mm','vias','opens','blocking','warnings','exclusions')}
  data=f.read_json(Path(row['result']))
  assert data['source_hashes']==protocol['freeze']['source_hashes'] and data['tools']==protocol['resume']['prior_freeze']['tools'] and p.sha(Path(row['result']))==row['result_sha256']
  if oldrow['accepted']:p.check_result(Path(row['result']))
  else:negative.append(raw_check(Path(row['result']),oldrow))
  row.update(native_accepted=oldrow['accepted'],whole_invocation_wall_seconds=oldrow['invocation_wall_seconds'],whole_invocation_full_cpu_seconds=oldrow['invocation_cpu_seconds']);rows.append(row)
 b2={'id':'B2_portfolio','status':summary['status'],'native_accepted':True,'selected':summary['selected'],'trials':summary['trials'],'pareto_frontier':summary['pareto_frontier'],'result':str(new/'portfolio/portfolio-summary.json'),'result_sha256':p.sha(new/'portfolio/portfolio-summary.json'),'whole_invocation_wall_seconds':newouter['combined_active_wall_seconds'],'whole_invocation_full_cpu_seconds':newouter['combined_full_cpu_seconds']};rows.insert(2,b2)
 def warnings(path):return f.canonical([x for x in f.read_json(path)['native']['findings'] if x['severity']=='warning'])
 assert warnings(Path(chosen['result']))==warnings(Path(rows[1]['result']))==warnings(Path(rows[3]['result']))
 report.update(status='completed',negative_controls=negative,unchanged_warning_signatures=True,original_shared_charge={'wall_seconds':base['shared_overhead_wall_seconds'],'full_cpu_seconds':base['shared_overhead_cpu_seconds']},original_outer_excess={'wall_seconds':oldouter['wall_seconds']-base['batch_wall_seconds'],'full_cpu_seconds':oldouter['full_cpu_seconds']-base['batch_cpu_seconds']},strong_B2_selected=chosen['id'],selected_B2_length_mm=chosen['length_mm'],C_length_mm=rows[3]['length_mm'],C_gain_vs_B2_mm=chosen['length_mm']-rows[3]['length_mm'])
except (Exception,KeyboardInterrupt) as exc:report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',comparison_eligible=False,reason=type(exc).__name__+': '+str(exc))
f.publish(out,report,stable,account,remaining,owned=lambda:h.owned_destination(owner))
# Complete write/readback is measured after the shared publication helper.
wall=time.monotonic()-START;cpu=time.process_time()+f.child_cpu()-CPU0
p.save_json(out/'execution.json',{'wall_seconds':wall,'full_cpu_seconds':cpu,'fixed_charge_seconds':CAP,'within_charged_allowance':max(wall,cpu)<CAP,'publication_included':True,'result_sha256':p.sha(out/'result.json'),'accounting_scope':'Complete foreground script from before implementation imports through canonical result write and readback; final small execution receipt publication also checked against the charged allowance.'})
try:
 h.owned_destination(owner);stable();assert f.read_json(out/'execution.json')['result_sha256']==p.sha(out/'result.json')
 if remaining()<=0:raise p.Rejected('final execution publication exceeded charge')
except (Exception,KeyboardInterrupt) as exc:
 report.update(status='invalidated',comparison_eligible=False,comparisons=[],reason=type(exc).__name__+': '+str(exc));f.publish(out,report,lambda:None,account,remaining,owned=lambda:h.owned_destination(owner))
finally:
 for sig,handler in previous.items():signal.signal(sig,handler)
print(json.dumps({k:report[k] for k in ('status','comparison_eligible','observed_audit_wall_seconds','observed_audit_full_cpu_seconds')}));raise SystemExit(0 if report['comparison_eligible'] else 2)
