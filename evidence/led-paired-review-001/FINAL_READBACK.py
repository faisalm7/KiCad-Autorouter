"""Bind supplemental004 to the already audited immutable native artifacts."""
from pathlib import Path
import ast,hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
RUN=ROOT/'.runs/push-button-led-native-paired-complete-sch-001'
BASE=ROOT/'.runs/push-button-led-native-paired-complete-sch-'
def read(path):return f.read_json(path)
def require(value,message):
 if not value:raise ValueError(message)
def digest(value):return hashlib.sha256(f.canonical(value).encode()).hexdigest()
old=read(HERE/'audit-001.json');prior=read(ROOT/'.runs/push-button-led-native-paired-complete-sch-002-qualification/result.json')
failed=read(ROOT/'.runs/push-button-led-native-paired-complete-sch-003-qualification/result.json');failedexecution=read(ROOT/'.runs/push-button-led-native-paired-complete-sch-003-qualification/execution.json')
amendpath=ROOT/'.runs/push-button-led-native-paired-complete-sch-004-qualification-protocol.json';amend=read(amendpath)
folder=ROOT/'.runs/push-button-led-native-paired-complete-sch-004-qualification';result=read(folder/'result.json');execution=read(folder/'execution.json');source=ROOT/'.runs/qualify-push-button-led-native-paired-complete-sch-004.py'
require(digest(pc.inventory(RUN,max_bytes=96*1024**2,max_files=16000,max_entries=32000,with_directories=True))==old['raw_run_inventory_sha256'],'audited native tree changed')
require(amend['prospective'] and amend['native_rerun'] is False and amend['strict_caps_unchanged']==120,'supplement changed scope')
for path,key in [('002-qualification/result.json','prior_qualified_result_sha256'),('003-qualification/result.json','prior_failed003_result_sha256'),('003-qualification/execution.json','prior_failed003_execution_sha256')]:
 require(p.sha(ROOT/('.runs/push-button-led-native-paired-complete-sch-'+path))==amend[key],'prior actual artifact changed')
require(amend['retained_prefix_charge_seconds']==sum(amend['prefix_breakdown_seconds'].values())==25 and amend['new_equal_charge_seconds']==15,'prior failure costs omitted')
require(p.sha(source)==amend['controller_sha256']==result['controller_sha256'] and p.sha(amendpath)==result['qualification_amendment_sha256'],'supplemental source changed')
require(result['status']=='completed' and result['comparison_eligible'] is True and result['accepted'] is False,'supplement did not qualify')
require(p.sha(folder/'result.json')==execution['result_sha256'] and execution['within_charged_allowance'] and max(execution['wall_seconds'],execution['full_cpu_seconds'])<execution['fixed_charge_seconds']==15,'complete supplement emission/cap differs')
require(failed['status']=='failed' and failed['comparison_eligible'] is False and failed['results']==[] and failed['reason'].startswith('AssertionError'),'failed003 was rewritten')
# Native/selection/effective source proof is byte-identical to qualified002.
for key in ['prospective_protocol_sha256','paired_summary_sha256','outer_execution_sha256','negative_final_candidates','C_trial_candidates','tools','source_sha256','strong_B2_selected','selected_B2_length_mm','C_length_mm','C_gain_vs_B2_mm','C_gain_vs_B1_mm','comparisons','unchanged_warning_signatures','paired_shared_charge','whole_outer_excess','shared_original_qualification_cost']:
 require(result[key]==prior[key],'supplement changed native/selection lineage: '+key)
costs={}
for row,previous in zip(result['results'],prior['results']):
 require(row['id']==previous['id'],'supplement changed arm order')
 changed={'charged_wall_seconds','charged_full_cpu_seconds'}
 require({k:v for k,v in row.items() if k not in changed}=={k:v for k,v in previous.items() if k not in changed},'supplement altered an arm witness')
 require(abs(row['charged_wall_seconds']-old['costs'][row['id']]['wall_seconds']-30)<1e-6 and abs(row['charged_full_cpu_seconds']-old['costs'][row['id']]['full_cpu_seconds']-30)<1e-6,'equal supplemental charges differ')
 require(max(row['charged_wall_seconds'],row['charged_full_cpu_seconds'])<120 and row['within_equal120_wall_full_cpu_caps'],'supplement exceeds cap')
 costs[row['id']]={k:row[k] for k in ['accepted','charged_wall_seconds','charged_full_cpu_seconds']}
# Execute only the corrected simple assertion AST against actual frozen metadata.
tree=ast.parse(source.read_text());condition=next(n.test for n in ast.walk(tree) if isinstance(n,ast.Assert) and "spec['audit_charge_seconds']" in ast.unparse(n.test))
spec=read(ROOT/'.runs/push-button-led-native-paired-complete-sch-001-protocol.json');protocol=read(RUN/'run/protocol.json')
require(eval(compile(ast.Expression(condition),str(source),'eval'),{'spec':spec,'CAP':15.,'ROOT':ROOT,'f':f,'protocol':protocol}) is True,'corrected separate metadata guards fail')
output={'schema':1,'native_execution':False,'actual_final_status':result['status'],'comparison_eligible':result['comparison_eligible'],'final_candidate_sha256':old['candidate_sha256'],'gain_vs_B2_mm':old['gain_vs_B2_mm'],'costs':costs,'prior_failure_retained':True,'failed003_reason':failed['reason'],'failed003_actual_execution':failedexecution,'new_audit_actual_execution':execution,'new_qualification_sha256':p.sha(folder/'result.json'),'new_controller_sha256':p.sha(source),'new_amendment_sha256':p.sha(amendpath),'corrected_assertion':ast.unparse(condition),'current_equal_caps':120,'claims_limit':result['claims_limit'],'accounting_limit':'Supplemental declared equal conservative allowances preserve raw unsampled supervisor windows; no exact complete-startup or speedup claim.'}
print(json.dumps(output,indent=2))
