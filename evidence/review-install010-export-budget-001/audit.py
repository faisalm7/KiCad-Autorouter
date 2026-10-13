"""Bounded retained installation and late cancellation audit, read only."""
from pathlib import Path
import sys,json,hashlib,ast,time,subprocess
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,review_export as e,review_view as rv,placement_clearance as pc,sexpr as sx
from scripts import install_smoke as install
I=ROOT/'.runs/installation-010';C=I/'checkout';W=ROOT/'.runs/installation-010-review-export';N=ROOT/'.runs/review-export-final-stage-cancel-budget-001'
def forbidden(*a,**k):raise AssertionError('Audit external execution prohibited')
def manifest(head):
 tree=ast.parse((ROOT/'autorouter/pipeline.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='tool_manifest')
 for node in fn.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='git_head' for t in node.targets):node.value=ast.Constant(head)
 scope=p.__dict__.copy();exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<manifest-recorded-head-only>','exec'),scope);return scope['tool_manifest']
def main():
 start=time.monotonic();sources={str(x.relative_to(ROOT)):p.sha(x) for x in sorted((ROOT/'autorouter').glob('*.py'))};ir=f.read_json(I/'result.json');wr=f.read_json(W/'result.json');control=f.read_json(N/'control.json');expected=f.read_json(I/'source-tracked.json');assert p.sha(I/'source-tracked.json')==ir['source_inventory_sha256']
 listing=(I/'07-clone-files.log').read_text();assert listing==(I/'03-source-files.log').read_text();clone_before=install.tracked_inventory(C,listing);assert clone_before==expected;root_before=install.tracked_inventory(ROOT,listing);diff={k:{'installed':expected[k],'current':v} for k,v in root_before.items() if expected[k]!=v};assert 'autorouter/review_export.py' in diff
 assert len(ir['commands'])==20 and ir['passed'] is True and ir['status']=='passed';assert 'Ran 763 tests' in (I/'13-tests.log').read_text() and (I/'13-tests.log').read_text().rstrip().endswith('OK')
 assert ir['git_head']==wr['installation_head']=='d1c40cc64a97dde7f0b6e85eafbfaeb012cec040';assert install.git_identity(C,ir['git_head'])==ir['git_identity_witnesses'][str(C)]
 observations=[]
 for step in ir['commands']:
  assert step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] is True and step['log_truncated'] is False and p.sha(Path(step['log']))==step['log_sha256'] and Path(step['log']).stat().st_size==step['log_bytes']
  observations.append({'name':step['name'],'pid':step['pid'],'wall_seconds':step['wall_seconds'],'cpu_seconds':step['cpu_seconds'],'log_sha256':step['log_sha256']})
 freshness=list(I.glob('freshness-*.json'));assert len(freshness)==8
 for path in freshness:
  step=f.read_json(path);assert step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] is True and step['log_truncated'] is False and p.sha(Path(step['log']))==step['log_sha256']
 assert abs(sum(s['cpu_seconds']+s['monitor_cpu_seconds'] for s in ir['commands'])-ir['command_cpu_seconds'])<1e-6 and ir['total_cpu_seconds']>=ir['command_cpu_seconds'] and ir['wall_seconds']<600
 receipt=Path(ir['native_receipt']['path']);assert p.sha(receipt)==ir['native_receipt']['sha256'];native=f.read_json(receipt);assert native['candidate_sha256']==ir['check_result']['candidate_sha256']==wr['candidate_sha256'];assert native['native']==ir['native']['native'];assert native['native']['warnings']==0 and p.native_accepted(native['native'])
 proof_path=Path(wr['export_path']);proof=f.read_json(proof_path);review_path=C/'.runs/install-review-export-010/review.json';review=f.read_json(review_path);review_tree=e.witness(review_path.parent);export_tree=e.witness(proof_path.parent);native_tree=e.witness(receipt.parent);assert p.sha(proof_path)==wr['export_proof_sha256'] and proof['candidate_sha256']==wr['candidate_sha256'] and proof['native_report_sha256']==wr['native_report_sha256']
 with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
  # Scope only to actual installed paths/pins, not current root source qualification.
  installed_manifest=manifest(ir['git_head'])
  with patch.object(c,'ROOT',C),patch.object(c,'JAR',C/'.tools/freerouting-2.5.0.jar'),patch.object(h,'__file__',str(C/'autorouter/handoff.py')),patch.object(p,'tool_manifest',installed_manifest):
   assert p.check_result(receipt)['current'] is True;installed_check=e._check_export(proof_path,lambda:None);assert installed_check['current'] is True
   binding,report=e.bind(C/'.runs/install-intent-010/choice.json');rejection=f.read_json(C/'.runs/install-reject-010/choice.json');assert rejection['choice']=='reject' and rejection['choice_recorded'] is True and rejection['routing_accepted'] is False and rejection['review_sha256']==p.sha(review_path) and rejection['receipt_sha256']==p.sha(receipt)
   for s in review['preview']['steps']:
    raw=f.read_json(review_path.parent/'plot-work'/(s['name']+'-process.json'));assert raw==s and raw['status']=='success' and raw['exit_code']==0 and raw['cleanup_complete'] is True;rv.svg_bytes(Path(s['argv'][s['argv'].index('--output')+1]))
   assert review['preview']['files']==wr['plots'];assert len(review['preview']['steps'])==4
  # New root cancellation after two completed native stages, no positive proof.
  assert control['controls_passed'] is True and control['controller_sha256']==p.sha(ROOT/'.runs/review-export-final-stage-cancel-budget-001.py')
  assert manifest(control['tools']['git_head'])()==control['tools']
  for path,w in control['original_inputs'].items():assert e.witness(Path(path))==w
  cancelled=f.read_json(N/'export/export.json');assert p.sha(N/'export/export.json')==control['cancelled_proof_sha256'] and cancelled['status']=='cancelled' and cancelled['export_accepted'] is False and cancelled['budget_seconds']==cancelled['cpu_budget_seconds']==120
  p.check_resource_accounting(cancelled,child_key='child_step_cpu_seconds');assert [s['name'] for s in cancelled['steps']]==['refill-drc','floor-final','final-drc']
  binding,report=e.bind(N/'intent/choice.json');basis,contract,layers=e.lineage(binding,report);source=Path(binding['source']);directory=N/'export/validation';candidate=directory/'candidate'/source.name;before=sx.read(Path(binding['validated_candidate']));expected_refill=dict(binding['source_hashes']);expected_refill[source.name]=binding['validated_candidate_sha256'];refill=directory/'refill'/source.name
  refill_native=f.check_drc_stage(directory,cancelled,'refill-drc',refill,refill,True,expected_refill);assert p.native_accepted(refill_native) and refill_native['warnings']==0
  assert pc.read_bytes(candidate)==(sx.dump(p.transplant_fill(before,sx.read(refill)))+'\n').encode();candidate_sha=p.sha(candidate)
  # The following helper input is observed readback metadata, not a claimed final receipt.
  stage_data=dict(cancelled,source_hashes=binding['source_hashes'],candidate_sha256=candidate_sha);f.check_final_context(directory,stage_data,p.preflight(source),candidate,[],contract,guidance_basis=basis)
  failure=f.read_json(directory/'final-drc-failure.json');process=f.read_json(directory/'final-drc-process.json');assert process==cancelled['steps'][-1]==control['process'] and process['status']=='cancelled' and process['exit_code']==-15 and process['cancel_signal']=='SIGTERM' and process['cleanup_complete'] is True
  assert control['observed'][0]['live_group']==process['pid'] and control['observed'][0]['native_stage']=='final-drc' and control['observed'][0]['signal']=='SIGTERM'
  expected_final=dict(binding['source_hashes']);expected_final[source.name]=candidate_sha;assert failure['binding']['before']==failure['binding']['after']==expected_final and failure['binding']==f.read_json(directory/'final-drc-binding.json') and failure['passed'] is False and failure['phase']=='native' and failure['artifacts']['final-drc.json'] is None and failure['capture_errors']==[] and pc.inventory(directory/'final-drc-input')==expected_final
  assert not (directory/'final-drc.json').exists() and not (directory/'metrics.json').exists();assert e.witness(directory/'snapshot',project=True)==binding['input_witnesses'][str(source.parent)]
  assert pc.inventory(directory/'code')=={Path(n).name:v for n,v in control['tools']['implementation_sha256'].items()}
  for step in cancelled['steps']:assert all(step.get(k)==v for k,v in f.read_json(directory/(step['name']+'-process.json')).items())
 for step in wr['commands']:
  raw=step['process'];assert raw['status']=='success' and raw['exit_code']==0 and raw['cleanup_complete'] is True and p.sha(Path(raw['log']))==step['log_sha256'];assert raw['argv'][3]==str(C/'.venv/bin/python')
 assert [s['name'] for s in wr['commands']]==['review-copy','accept-intent','export','check','reject-intent'];assert wr['within_budget'] is True and max(wr['wall_seconds'],wr['total_cpu_seconds'])<=180
 assert e.witness(review_path.parent)==review_tree and e.witness(proof_path.parent)==export_tree and e.witness(receipt.parent)==native_tree and install.tracked_inventory(C,listing)==clone_before and install.tracked_inventory(ROOT,listing)==root_before and all(p.sha(ROOT/n)==v for n,v in sources.items())
 output={'schema':1,'status':'retained_installation_and_new_cancel_verified','installation_head':ir['git_head'],'clone_tracked_file_count':len(expected),'clone_exact_frozen_tracked_map':True,'current_root_diff_from_installed_map':diff,'current_exporter_sha256':sources['autorouter/review_export.py'],'installed_exporter_sha256':expected['autorouter/review_export.py'],'installation_commands':observations,'additional_freshness_records':len(freshness),'fullsuite_retained_log_count':763,'installation_native':{'candidate_sha256':native['candidate_sha256'],'native_report_sha256':native['native_report_sha256'],'native_counts':{k:native['native'][k] for k in ('opens','blocking','warnings','exclusions')},'metrics':native['metrics'],'native_steps':[s['name'] for s in native['steps']]},'installed_workflow':{'commands':len(wr['commands']),'plots':len(review['preview']['steps']),'native_export_steps':[s['name'] for s in proof['steps']],'native_counts':{k:proof['native'][k] for k in ('opens','blocking','warnings','exclusions')},'candidate_sha256':proof['candidate_sha256'],'export_proof_sha256':p.sha(proof_path),'strict_check_scoped_to_installed_paths':installed_check,'root_postinstall_source_qualification_claimed':False},'late_cancel':{'actual_head':control['tools']['git_head'],'budget_seconds':cancelled['budget_seconds'],'cpu_budget_seconds':cancelled['cpu_budget_seconds'],'shared_resource_accounting_passed':True,'completed_refill_native_counts':{k:refill_native[k] for k in ('opens','blocking','warnings','exclusions')},'completed_floor_context_binding_passed':True,'cancelled_stage':process['name'],'exit_code':process['exit_code'],'cancel_signal':process['cancel_signal'],'cleanup_complete':process['cleanup_complete'],'no_final_report':True,'positive_proof':False,'original_inputs_exact':True,'candidate_sha256_readback':candidate_sha,'cancelled_proof_sha256':p.sha(N/'export/export.json'),'code_snapshot_exact':True,'algorithm_entry_established':False},'recorded_costs':{'installation':{k:ir[k] for k in ('wall_seconds','total_cpu_seconds','command_cpu_seconds')},'installed_workflow':{k:wr[k] for k in ('wall_seconds','total_cpu_seconds')},'late_cancel':{k:control[k] for k in ('wall_seconds','full_cpu_seconds')}},'cost_scope':'Stored samples; installation receipt explicitly precedes final publication checks. Installed workflow initial tracked scan precedes its timer, final tracked scan/publication follows sample. Late control source witness precedes timer and final tool-manifest/publication follows sample. These are not exact full-envelope comparative totals. No native cost omitted from stored receipt algebra.','source_and_evidence_unchanged':True,'reviewer_subprocess_Git_native_JVM_network_executed':False,'audit_wall_seconds':time.monotonic()-start}
 (HERE/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(json.dumps({'files':len(expected),'installed_head':ir['git_head'],'root_differences':list(diff),'cancel_accounting_pass':True,'seconds':output['audit_wall_seconds']}))
if __name__=='__main__':main()
