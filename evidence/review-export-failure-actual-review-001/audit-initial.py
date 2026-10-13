"""Read-only failure-control audit; no actual external execution."""
from pathlib import Path
import sys,json,hashlib,ast,subprocess,time
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
from autorouter import pipeline as p,handoff as h,floor_route as f,review_export as e,placement_strategy as ps,placement_clearance as pc,sexpr as sx
from autorouter import config as c
A=ROOT/'.runs/review-export-controls-001';B=ROOT/'.runs/review-export-controls-continuation-001';EA=ROOT/'.runs/review-export-controls-execution-001';EB=ROOT/'.runs/review-export-controls-continuation-execution-001'
def forbidden(*a,**k):raise AssertionError('External execution prohibited')
def main():
 start=time.monotonic();sources={str(x.relative_to(ROOT)):p.sha(x) for x in [*sorted((ROOT/'autorouter').glob('*.py')),ROOT/'toolchain.lock.json']};before={str(x):e.witness(x) for x in (A,B,EA,EB)}
 prior=f.read_json(A/'result.json');record=f.read_json(B/'result.json');ea=f.read_json(EA/'execution.json');eb=f.read_json(EB/'execution.json');assert prior['status']=='failed' and prior['controls_passed'] is False and prior['reason']=="TypeError: parse_report() missing 1 required positional argument: 'board_name'";assert record['status']=='completed' and record['controls_passed'] is True and record['accepted'] is False
 assert record['prior_inventory']==before[str(A)] and record['prior_execution']==ea
 for path,w in prior['original_inputs'].items():assert e.witness(Path(path))==w
 for driver,wrapper,execution in [('review-export-native-controls-001.py','run-review-export-controls-001.py',ea),('review-export-native-controls-continuation-001.py','run-review-export-controls-continuation-001.py',eb)]:
  assert p.sha(ROOT/'.runs'/driver)==execution['controller_sha256'];assert p.sha(ROOT/'.runs'/wrapper)==execution['wrapper_sha256'];assert p.sha(Path(execution['process']['log']))==execution['log_sha256'];assert execution['process']['cleanup_complete'] is True and execution['process']['log_truncated'] is False
 assert ea['process']['exit_code']==2 and eb['process']['exit_code']==0 and ea['git_head']==eb['git_head']==record['tools']['git_head']
 # Compute real current pins via original manifest body, substituting only its Git lookup.
 tree=ast.parse((ROOT/'autorouter/pipeline.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='tool_manifest')
 for node in fn.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in node.targets):node.value=ast.Constant(record['tools']['git_head'])
 scope=p.__dict__.copy();exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<manifest-recorded-head-only>','exec'),scope);manifest=scope['tool_manifest']
 checks=[];processes=[]
 with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden),patch.object(p,'tool_manifest',manifest):
  assert manifest()==prior['tools']==record['tools']
  # Real GUI metadata edit was recorded in intent; original rules remain authority.
  folder=A/'gui_rule_metadata';proof=f.read_json(folder/'export/export.json');checked=e._check_export(folder/'export/export.json',lambda:None);assert checked['current'] is True
  binding,report=e.bind(folder/'intent/choice.json');source=Path(binding['source']);gui_project=folder/'review/project'/source.with_suffix('.kicad_pro').name;native_project=Path(proof['project_file']);original_project=source.with_suffix('.kicad_pro')
  original=f.read_json(original_project);gui=f.read_json(gui_project);assert gui['board']['design_settings']['rule_severities']['clearance']=='ignore';assert original['board']['design_settings']['rule_severities']['clearance']!='ignore';assert p.sha(native_project)==p.sha(original_project)!=p.sha(gui_project)
  checks.append({'name':'gui_rule_metadata','original_project_sha256':p.sha(original_project),'gui_project_sha256':p.sha(gui_project),'export_project_sha256':p.sha(native_project),'fresh_export_proof_current_under_actual_source_and_recorded_HEAD':True,'native_counts':{k:proof['native'][k] for k in ('opens','blocking','warnings','exclusions')}})
  # Stale choice fails using current binder before any output exists.
  folder=A/'stale_board';choice=f.read_json(folder/'intent/choice.json');board=folder/'review/project'/source.name;assert p.sha(folder/'before-board.kicad_pcb')==choice['validated_candidate_sha256'] and p.sha(board)!=choice['validated_candidate_sha256'] and board.read_bytes()==(folder/'before-board.kicad_pcb').read_bytes()+b'\n';assert not (folder/'export').exists()
  try:e.bind(folder/'intent/choice.json')
  except p.Rejected as exc:stale=str(exc)
  else:raise AssertionError('stale intent accepted')
  assert stale==prior['cases'][1]['reason'];checks.append({'name':'stale_board','rejection':stale,'native_steps':0,'output_exists':False,'source_routing_unchanged':True})
  # Actual invalid derivative, exact one via removal and shared native checks.
  folder=A/'missing_required_via';proof=f.read_json(folder/'export/export.json');binding,report=e.bind(folder/'intent/choice.json');basis,contract,layers=e.lineage(binding,report);before_tree=sx.read(Path(binding['validated_candidate']));vias=sx.children(before_tree,'via');assert len(vias)==1;removed=vias[0];before_tree.remove(removed);candidate=Path(proof['candidate']);directory=folder/'export/validation'
  result=ps.check_candidate_stage(directory,proof,p.preflight(Path(binding['source'])),binding['source_hashes'],basis,before_tree)
  native=p.parse_report(directory/'final-drc.json',source.name);assert native==proof['native'] and native['opens']==1 and native['blocking']==0 and native['warnings']==2 and not p.native_accepted(native)
  assert p.routes(sx.read(candidate))==p.routes(before_tree);assert proof['export_accepted'] is False and proof['status']=='rejected';assert p.sha(candidate)==proof['candidate_sha256'] and p.sha(directory/'final-drc.json')==proof['native_report_sha256'];p.check_resource_accounting(proof,child_key='child_step_cpu_seconds')
  assert e.witness(directory/'snapshot',project=True)==binding['input_witnesses'][str(Path(binding['source']).parent)]
  checks.append({'name':'missing_required_via','candidate_sha256':proof['candidate_sha256'],'native_report_sha256':proof['native_report_sha256'],'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'exactly_one_original_validated_via_removed':True,'other_route_records_and_immutable_design_exact':True,'shared_native_context_metrics_DRC_bindings_pass':True,'export_accepted':False,'export_error':proof['error'],'derivative_native_quality_not_accepted':True})
  # Actual SIGTERM attempt, no final DRC or positive proof.
  folder=B/'cancel_native';proof=f.read_json(folder/'export/export.json');binding,report=e.bind(folder/'intent/choice.json');directory=folder/'export/validation';process=f.read_json(directory/'refill-drc-process.json');failure=f.read_json(directory/'refill-drc-failure.json');observation=record['cases'][3]['observed'];assert len(observation)==1 and observation[0]['live_native_group']==process['pid'] and observation[0]['signal_target']==eb['process']['pid'] and observation[0]['signal']=='SIGTERM'
  assert process['status']=='cancelled' and process['cancel_signal']=='SIGTERM' and process['exit_code']==-15 and process['cleanup_complete'] is True and process['signal_cancellation_enabled'] is True and process['log_truncated'] is False
  assert proof['status']=='cancelled' and proof['export_accepted'] is False and proof['error']=='KeyboardInterrupt: ' and proof['steps']==[process] and failure['passed'] is False and failure['phase']=='native' and failure['error']['type']=='KeyboardInterrupt'
  assert record['cases'][3]['proof_sha256']==p.sha(folder/'export/export.json') and record['cases'][3]['live_group_gone'] is True
  expected=dict(binding['source_hashes']);expected[source.name]=binding['validated_candidate_sha256'];assert failure['binding']==f.read_json(directory/'refill-drc-binding.json') and failure['binding']['before']==failure['binding']['after']==expected and failure['validation_copy_before']==expected and pc.inventory(directory/'refill')==expected
  assert not (directory/'refill-drc.json').exists() and not (directory/'final-drc.json').exists();assert failure['artifacts']['refill-drc.json'] is None and failure['capture_errors']==[]
  argv=[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(directory/'refill-drc.json'),'--save-board',str(directory/'refill'/source.name)];assert process['argv']==argv and process['cwd']==str(directory)
  p.check_resource_accounting(proof,child_key='child_step_cpu_seconds')
  checks.append({'name':'cancel_native','status':proof['status'],'export_accepted':False,'native_attempt_only':True,'no_native_report':True,'signal':process['cancel_signal'],'native_process_pid':process['pid'],'controller_signal_pid':observation[0]['signal_target'],'cleanup_complete':True,'live_group_gone_observed_by_original_controller':True,'positive_proof_rejected':True,'failure_sha256':p.sha(directory/'refill-drc-failure.json')})
  for folder in (A/'gui_rule_metadata/export',A/'missing_required_via/export',B/'cancel_native/export'):
   proof=f.read_json(folder/'export.json')
   for step in proof['steps']:
    raw=f.read_json(folder/'validation'/(step['name']+'-process.json'));assert all(step.get(k)==v for k,v in raw.items());assert set(step)-set(raw)<={'validated_input_sha256','emitted_candidate'};assert Path(step['log']).stat().st_size==step['log_bytes'];processes.append({'case':folder.parent.name,'name':step['name'],'pid':step['pid'],'status':step['status'],'exit_code':step['exit_code'],'process_sha256':p.sha(folder/'validation'/(step['name']+'-process.json')),'log_sha256':p.sha(Path(step['log'])),'cpu_seconds':step['cpu_seconds'],'wall_seconds':step['wall_seconds']})
 assert len(processes)==9 and len({s['pid'] for s in processes})==9
 assert record['cumulative_wall_seconds']==ea['wall_seconds']+record['wall_seconds'] and record['cumulative_full_cpu_seconds']==ea['full_cpu_seconds']+record['total_cpu_seconds']
 outer={'wall_seconds':ea['wall_seconds']+eb['wall_seconds'],'full_cpu_seconds':ea['full_cpu_seconds']+eb['full_cpu_seconds']};assert max(outer.values())<300
 assert all(e.witness(Path(k))==v for k,v in before.items()) and all(p.sha(ROOT/n)==v for n,v in sources.items())
 output={'schema':1,'status':'retained_actual_controls_verified','actual_head':record['tools']['git_head'],'original_failed_controller_status_preserved':prior['status'],'original_failure_reason':prior['reason'],'prior_inventory_files':len(record['prior_inventory']['files']),'prior_inventory_directories':len(record['prior_inventory']['directories']),'original_project_and_routing_inputs_unchanged':True,'all_actual_artifacts_and_source_stable_before_after':True,'checks':checks,'processes':processes,'unique_native_processes':len(processes),'outer_cumulative_cost':outer,'inner_cumulative_cost':{k:record[k] for k in ('cumulative_wall_seconds','cumulative_full_cpu_seconds')},'source_hashes':sources,'controller_source_hashes':{n:p.sha(ROOT/'.runs'/n) for n in ('review-export-native-controls-001.py','review-export-native-controls-continuation-001.py')},'actual_result_hashes':{str(q.relative_to(ROOT)):p.sha(q) for q in (A/'result.json',B/'result.json',EA/'execution.json',EB/'execution.json')},'reviewer_native_Git_subprocess_network_executed':False,'audit_wall_seconds':time.monotonic()-start,'scope':'Owned failure seams with actual native work, one exposed placement fixture. No rerouted original, GUI live-editor, broader board or physical validation claim. Cancelled worker never emitted native DRC report; controller-recorded group disappearance is historical evidence, not new PID probing.'}
 (HERE/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'native_processes':len(processes),'outer':outer,'seconds':output['audit_wall_seconds']}))
if __name__=='__main__':main()
