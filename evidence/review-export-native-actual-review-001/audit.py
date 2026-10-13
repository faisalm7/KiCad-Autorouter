"""Read-only retained native evidence audit; no external execution."""
from pathlib import Path
from collections import Counter
from unittest.mock import patch
import ast,hashlib,json,sys,time,subprocess
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
from autorouter import config as c,pipeline as p,floor_route as f,review_export as e,handoff as h,review_view as rv,placement_clearance as pc,sexpr as sx
RUN=ROOT/'.runs/review-export-native-001/run';HEAD='470bd4aa63ed928d8a1669284d5db3dd61d91d98'
def reject(*a,**kw):raise AssertionError('External execution prohibited in read-only audit')
def read(x):return f.read_json(x)
def main():
 start=time.monotonic();source={str(x.relative_to(ROOT)):p.sha(x) for x in [*sorted((ROOT/'autorouter').glob('*.py')),ROOT/'scripts/qualify_review_export.py',ROOT/'toolchain.lock.json']};before=e.witness(RUN)
 summary=read(RUN/'result.json');execution=read(RUN.parent/'execution.json');rows=[];processes=[]
 # Only the manifest function's Git lookup is replaced with the recorded invocation HEAD.
 # All tool and actual CURRENT code hashes are still computed by its original body.
 tree=ast.parse((ROOT/'autorouter/pipeline.py').read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='tool_manifest')
 for node in fn.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in node.targets):node.value=ast.Constant(HEAD)
 module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));scope=p.__dict__.copy();exec(compile(module,'<actual-manifest-recorded-head-only>','exec'),scope);actual_manifest=scope['tool_manifest']
 with patch.object(subprocess,'run',reject),patch.object(subprocess,'Popen',reject),patch.object(p,'tool_manifest',actual_manifest):
  current=actual_manifest()
  for entry in summary['cases']:
   name=entry['name'];case=RUN/name;data=read(case/'export/export.json');report=read(Path(data['inputs']['receipt']));review=read(case/'review/review.json');choice=read(case/'intent/choice.json');rejection=read(case/'rejection/choice.json')
   assert all(p.sha(case/rel)==entry[key] for rel,key in [('review/review.json','review_sha256'),('intent/choice.json','choice_sha256'),('export/export.json','export_sha256'),('rejection/choice.json','rejection_sha256')])
   binding,bound_report=e.bind(case/'intent/choice.json');assert binding==data['inputs'] and bound_report==report
   basis,contract,layers=e.lineage(binding,report);candidate=e.check_stage(case/'export/validation',data,binding,report,basis,contract,layers)
   assert e.evidence(case/'export')==data['export_evidence']
   assert e.witness(case/'export/validation/snapshot',project=True)==binding['input_witnesses'][str(Path(binding['source']).parent)]
   code={Path(k).name:v for k,v in data['tools']['implementation_sha256'].items()};assert pc.inventory(case/'export/validation/code')==data['code_inventory']==code
   assert all(p.sha(Path(path))==digest for path,digest in data['tools']['files'].items())
   runtime_diff={k:{'recorded':v,'current':h.runtime_inventory().get(k)} for k,v in data['runtime_source_sha256'].items() if h.runtime_inventory().get(k)!=v}
   changed={k:{'recorded':v,'current':current['implementation_sha256'].get(k)} for k,v in data['tools']['implementation_sha256'].items() if current['implementation_sha256'].get(k)!=v}
   assert set(changed)=={'autorouter/floor_route.py'}
   assert all(not x.get(k) for x in (review,choice,rejection) for k in ('routing_accepted','applied','native_validation_performed','human_pcb_approval_observed'))
   assert rejection['choice']=='reject' and rejection['choice_recorded'] is True and rejection['status']=='disposition_recorded' and rejection['candidate_board_unchanged'] is True and rejection['within_budget'] is True
   assert rejection['review_sha256']==p.sha(case/'review/review.json') and rejection['receipt_sha256']==p.sha(Path(binding['receipt']))
   assert rejection['original_source_hashes']==binding['source_hashes'] and rejection['routing_evidence_hashes']==choice['routing_evidence_hashes'] and rejection['observed_review_project_hashes']==choice['observed_review_project_hashes']
   assert all(rejection[k]<=30 and e.finite(rejection[k]) for k in ('wall_seconds','total_cpu_seconds'))
   for step in data['steps']:
    raw_process=read(case/'export/validation'/(step['name']+'-process.json'));assert all(step.get(k)==v for k,v in raw_process.items());assert set(step)-set(raw_process)<= {'validated_input_sha256','emitted_candidate'}
    assert step['cleanup_complete'] is True and step['log_truncated'] is False and step['signal_cancellation_enabled'] is True
    processes.append({'case':name,'stage':step['name'],'pid':step['pid'],'status':step['status'],'exit_code':step['exit_code'],'wall_seconds':step['wall_seconds'],'cpu_seconds':step['cpu_seconds'],'log_sha256':p.sha(Path(step['log']))})
   preview=review.get('preview');preview_rows=[]
   if preview:
    for step in preview['steps']:
     assert read(case/'review/plot-work'/(step['name']+'-process.json'))==step
     assert step['cleanup_complete'] is True and step['status']=='success' and step['exit_code']==0 and step['log_truncated'] is False
     assert Path(step['log']).stat().st_size==step['log_bytes']
     assert step['argv'][:4]==[*f.SANDBOX,str(c.CLI)] and step['argv'][4:7]==['pcb','export','svg']
     input_board=Path(step['argv'][-1]);original_tree=binding['source_hashes'] if step['name'].startswith('before-') else binding['candidate_hashes']
     input_binding=read(case/'review/plot-work'/(step['name']+'-input-binding.json'));assert input_binding['before']==original_tree and input_binding['after']==pc.inventory(input_board.parent);assert input_binding['input']==str(input_board);p.check_drc_project(input_binding['before'],input_binding['after'],input_board.name)
     rawsvg=Path(step['argv'][step['argv'].index('--output')+1]);rv.svg_bytes(rawsvg)
     preview_rows.append({'name':step['name'],'process_sha256':p.sha(case/'review/plot-work'/(step['name']+'-process.json')),'raw_svg_sha256':p.sha(rawsvg),'log_sha256':p.sha(Path(step['log']))})
     processes.append({'case':name,'stage':step['name'],'pid':step['pid'],'status':step['status'],'exit_code':step['exit_code'],'wall_seconds':step['wall_seconds'],'cpu_seconds':step['cpu_seconds'],'log_sha256':p.sha(Path(step['log']))})
   rows.append({'name':name,'schema':report['schema'],'policy':binding['input_policy'],'receipt_sha256':binding['receipt_sha256'],'candidate_sha256':p.sha(candidate),'final_native_report_sha256':p.sha(case/'export/validation/final-drc.json'),'export_sha256':p.sha(case/'export/export.json'),'native':data['native'],'metrics':data['metrics'],'export_compute':{k:data.get(k) for k in ('budget_seconds','wall_seconds','total_cpu_seconds','parent_cpu_seconds','child_step_cpu_seconds','control_child_cpu_seconds','monitor_cpu_seconds')},'original_routing_compute':data['original_routing_receipt_compute'],'export_stage_names':[s['name'] for s in data['steps']],'whole_project_drc_clean':data['whole_project_drc_clean'],'preview_raw_bindings':preview_rows,'rejection_sha256':p.sha(case/'rejection/choice.json'),'shared_original_rule_native_process_geometry_protected_layers_checks_pass':True,'historical_complete_tree_and_original_snapshot_exact':True,'current_implementation_difference':changed,'current_runtime_difference':runtime_diff})
  # Honest strict-current readback: no historical-manifest waiver.
  try:e._check_export(RUN/'native_partial_layers/export/export.json',lambda:None)
  except p.Rejected as exc:current_rejection=str(exc)
  else:raise AssertionError('Historical export unexpectedly accepted as current despite publisher changes')
 assert len({x['pid'] for x in processes})==len(processes)
 assert e.witness(RUN)==before
 assert all(p.sha(ROOT/n)==v for n,v in source.items())
 assert summary['controls_passed'] is True and all(x['passed'] is True for x in summary['cases'])
 assert execution['git_head']==HEAD and execution['process']['cleanup_complete'] is True and execution['log_sha256']==p.sha(RUN.parent/'command.log') and execution['process']['exit_code']==0
 assert execution['wall_seconds']>=execution['process']['wall_seconds']>=summary['wall_seconds'] and execution['full_cpu_seconds']>=summary['total_cpu_seconds']
 output={'schema':1,'kind':'independent-retained-review-export-native-evidence-audit','actual_head':HEAD,'actual_controller_sha256':summary['controller_sha256'],'current_sources':source,'actual_run_tree':{'files':len(before['files']),'directories':len(before['directories']),'sha256':hashlib.sha256(f.canonical(before).encode()).hexdigest()},'source_and_actual_evidence_unchanged':True,'current_strict_export_rejected':current_rejection,'cases':rows,'processes':processes,'unique_fresh_export_and_preview_processes':len(processes),'outer_compute':{'wall_seconds':execution['wall_seconds'],'full_cpu_seconds':execution['full_cpu_seconds'],'inner_wall_seconds':summary['wall_seconds'],'inner_cpu_seconds':summary['total_cpu_seconds']},'scope':'Retained five fresh native exports and four pruning copper plots only. Current helper staleness preserved; no native rerun, no solver, no stale/cancel/invalid export qualification, GUI live application, human PCB approval or physical electrical approval.','read_only_audit_seconds':time.monotonic()-start,'external_execution_by_auditor':False}
 (HERE/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(json.dumps({'cases':len(rows),'processes':len(processes),'current_rejection':current_rejection,'seconds':output['read_only_audit_seconds']}))
if __name__=='__main__':main()
