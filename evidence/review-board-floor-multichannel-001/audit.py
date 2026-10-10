"""Read-only full-board rejected-run audit; no native/engine execution."""
from pathlib import Path
from collections import Counter
import datetime,hashlib,importlib.util,json,math,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,board_floor as g,floor_route as f,sexpr as sx
PARSER=ROOT/'.runs/review-board-floor-production-native-001/audit.py'
spec=importlib.util.spec_from_file_location('reviewed_ses_parser',PARSER);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
RUN=ROOT/'.runs/board-floor-multichannel-001'
def raw(name):return json.loads((RUN/name).read_text())
def main():
 before=json.loads((HERE/'before.json').read_text());inventory=p.tree_hash(RUN);d=raw('result.json');source=Path(d['source']);candidate=Path(d['candidate']);original=sx.read(source);current=sx.read(candidate);task=g.task_from_source(original);checks={}
 def check(name,condition):checks[name]=bool(condition);assert condition,name
 check('source_snapshot_unchanged',p.tree_hash(source.parent)==before['source_inventory']==d['source_hashes']==p.tree_hash(RUN/'snapshot'))
 check('actual_rejected_not_relabelled',d['accepted'] is False and d['status']=='drc_rejected' and d['input_policy']==f.POLICY)
 try:p.check_result(RUN/'result.json')
 except p.Rejected as exc:acceptance_rejection=str(exc)
 else:raise AssertionError('rejected result accepted by check_result')
 f.check_floor_result(RUN,d,original,candidate,[]);check('floor_transport_context_contract_passed_without_acceptance',True)
 p.verify_candidate_files(candidate,d['source_hashes'],d['candidate_sha256']);check('all_candidate_project_files_original',True)
 check('immutable_geometry_and_constraints_equal',p.immutable(original)==p.immutable(current))
 def zones(tree):
  result={}
  for z in sx.children(tree,'zone'):
   node=[x for x in z if not isinstance(x,list) or not x or x[0] not in p.DERIVED_ZONE];result[sx.unquote(sx.one(z,'uuid')[1])]=node
  return result
 check('six_zone_intents_unchanged',len(zones(original))==6 and zones(original)==zones(current))
 project=source.with_suffix('.kicad_pro').read_bytes();check('project_rules_exact_in_every_native_copy',all((RUN/directory/source.with_suffix('.kicad_pro').name).read_bytes()==project for directory in ['snapshot','candidate','floor-export-input','source-drc-input','refill','final-drc-input']))
 context=raw('floor-export-context.json');native_final=raw('floor-final-context.json');rawdsn=(RUN/'native.dsn').read_bytes();guided=(RUN/'floor-guided.dsn').read_bytes();taskdsn=(RUN/'task.dsn').read_bytes();project_bytes=project;taskbytes=(sx.dump(task)+'\n').encode()
 g.verify_chain(rawdsn,guided,taskdsn,context,project_bytes,taskbytes);check('native_guidance_adapter_chain_exact',True)
 imported=sx.read(RUN/'imported.kicad_pcb');refill=sx.read(RUN/'refill'/source.name)
 check('exact_candidate_transport_and_saved_fill',candidate.read_bytes()==(sx.dump(p.transplant_fill(p.transplant_routes(task,imported),refill))+'\n').encode())
 ses=reader.ses_geometry(sx.read(RUN/'routes.ses'));geometry=reader.board_geometry(current)
 check('SES_import_candidate_geometry_equal',ses==reader.board_geometry(imported)==geometry)
 native_audit=g.audit_native_routes(current,native_final);check('native_actual_route_readback_exact',native_audit['passed'])
 reports={};parsed_reports={}
 for stage in ['source-drc','refill-drc','final-drc']:
  parsed=p.parse_report(RUN/(stage+'.json'),source.name);parsed_reports[stage]=parsed
  reports[stage]={**{key:parsed[key] for key in ['opens','blocking','warnings','exclusions']},'errors_by_type':dict(Counter(v['type'] for v in parsed['findings'] if v['severity']=='error'))}
  step=next(s for s in d['steps'] if s['name']==stage);check(stage+'_exit_matches_findings',step['exit_code']==(5 if parsed['findings'] else 0) and step['status']==('nonzero_exit' if parsed['findings'] else 'success'))
 final=parsed_reports['final-drc'];check('receipt_matches_raw_final_DRC',d['native']==final and d['native_report_sha256']==p.sha(RUN/'final-drc.json'))
 check('native_correctly_rejects',not p.native_accepted(final) and d['native_rejection_reasons']==p.native_rejection_reasons(final))
 check('recorded_failure_160opens_one_thermal_94warnings',final['opens']==160 and final['blocking']==1 and final['warnings']==94 and final['exclusions']==0 and reports['final-drc']['errors_by_type']=={'starved_thermal':1,'unconnected_items':160})
 binding=raw('final-drc-binding.json');expected=dict(d['source_hashes']);expected[candidate.name]=d['candidate_sha256'];native_input=RUN/'final-drc-input'/candidate.name
 check('final_native_input_bound',binding['source']==str(candidate) and binding['input']==str(native_input) and binding['saved'] is False and binding['before']==expected and binding['after']==p.tree_hash(native_input.parent))
 check('final_native_input_preserves_original_rules',all(binding['after'].get(k)==v for k,v in expected.items()) and not(set(binding['after'])-set(expected)-{candidate.with_suffix('.kicad_prl').name}))
 argv=[*f.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(RUN/'final-drc.json'),str(native_input)]
 f.process_check(RUN,d,'final-drc',argv,allowed=(5,));check('final_native_process_exact',True)
 step=next(s for s in d['steps'] if s['name']=='final-drc');check('final_step_bound',step['validated_input_sha256']==d['candidate_sha256'] and step['emitted_candidate']==str(candidate))
 settings=d['engine_budget'];check('same_declared_profile_reserves_and_flags',settings=={**p.engine_profile_settings('completion-only',settings['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True),'outer_task_wall_budget_seconds':120.0,'outer_task_cpu_budget_seconds':120.0})
 check('all_workers_network_denied_cleanup_complete',all(s['argv'][:len(f.SANDBOX)]==f.SANDBOX and s['cleanup_complete'] is True for s in d['steps']))
 total=d['parent_cpu_seconds']+sum(s['cpu_seconds']+s['monitor_cpu_seconds'] for s in d['steps'])+d['control_child_cpu_seconds'];check('resource_sums_and_caps',abs(total-d['total_cpu_seconds'])<1e-6 and total<=120 and sum(s['wall_seconds'] for s in d['steps'])<=d['wall_seconds']<=120 and d['budget_seconds']==d['cpu_budget_seconds']==120)
 length=sum(math.hypot(item[4][0]-item[5][0],item[4][1]-item[5][1])*count/1000000 for item,count in geometry.items() if item[0]=='segment');vias=sum(v for k,v in geometry.items() if k[0]=='via')
 check('independent_geometry_metrics_match',math.isclose(length,d['metrics']['track_length_mm'],abs_tol=1e-6) and vias==d['metrics']['vias']==0)
 actual_code={str(x.relative_to(ROOT)):p.sha(x) for x in sorted((ROOT/'autorouter').glob('*.py'))};retained_code={str(Path('autorouter')/Path(k).name):v for k,v in p.tree_hash(RUN/'code').items()};check('retained_code_matches_recorded_and_current',retained_code==d['tools']['implementation_sha256']==actual_code)
 old=p.parse_report(ROOT/'.runs/multichannel-native-001/final-drc.json',source.name);old_errors=dict(Counter(v['type'] for v in old['findings'] if v['severity']=='error'))
 check('previous_width_clearance_annulus_via_errors_absent_now',all(reports['final-drc']['errors_by_type'].get(kind,0)==0 for kind in ['track_width','clearance','annular_width','via_diameter']))
 check('no_audit_mutation',inventory==p.tree_hash(RUN)==before['run_inventory'] and before['source_inventory']==p.tree_hash(source.parent))
 return {'schema':1,'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'audit_passed':all(checks.values()),'routing_accepted':False,'check_result_expected_rejection':acceptance_rejection,'floor_helper_scope':'check_floor_result validates retained transformation/transport/context consistency even for rejected data; it is not routing acceptance and does not override native DRC.','checks':checks,'facts':{'git_head':d['tools']['git_head'],'candidate_sha256':d['candidate_sha256'],'project_sha256':p.sha(source.with_suffix('.kicad_pro')),'source_files':len(d['source_hashes']),'zones':6,'reports':reports,'prior_unmodified_adapter_error_counts':old_errors,'metrics':d['metrics'],'generated_route_widths_nm':sorted({r['width_nm'] for r in native_final['routes'] if r['kind']=='segment'}),'native_thermal_findings':[v for v in final['findings'] if v['type']=='starved_thermal'],'receipt_wall_seconds':d['wall_seconds'],'receipt_total_cpu_seconds':total,'peak_child_rss_bytes':d['peak_child_rss_bytes'],'engine_settings':settings},'run_inventory_sha256':hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'shared_SES_parser_sha256':p.sha(PARSER),'limitations':['Rejected full board:160 opens plus thermal violation; no usable completion or quality win.','Older unmodified run comparison is diagnostic, not a fresh equal-code/profile/timing causal comparison.','Zero vias on this failed full-board attempt; this run cannot qualify nonzero via transport, which was exercised separately by the owned fixture.','Stored totals precede final publication/readback. No independent enclosing invocation timer retained for this CLI run.','Original project/rules and six zone definitions preserved; native refill/final DRC actually ran with residual thermal reported. No claim of electrical/manufacturing adequacy.','Read-only AI evidence review, not authentication, fresh native execution or human PCB review.']}
if __name__=='__main__':
 path=HERE/'audit.json'
 if path.exists():raise SystemExit('refuse collision')
 try:result=main()
 except Exception as exc:result={'schema':1,'audit_passed':False,'routing_accepted':False,'error':type(exc).__name__+': '+str(exc)}
 with path.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({k:result[k] for k in ['audit_passed','routing_accepted','error'] if k in result}));raise SystemExit(0 if result['audit_passed'] else 1)
