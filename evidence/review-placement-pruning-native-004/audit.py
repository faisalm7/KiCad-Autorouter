"""Read-only independent audit of recorded native pruning controls; never launches tools.
All native checks below interpret retained real process/report/input artifacts.
No freshly executed native result, matched comparison or family gain is claimed.
"""
from pathlib import Path
from collections import Counter
import copy,hashlib,json,math,sys,time,subprocess
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,placement_clearance as pc,placement_strategy as ps,sexpr as sx,strategy as s
from experiments.placement_pruning_controls_v1 import driver as control
run=ROOT/'.runs/placement-pruning-controls-004/run';readonly=ROOT/'.runs/placement-pruning-controls-004-readback-001'
start=time.monotonic();cpu=time.process_time();checks=[]
def must(value,label):
 if not value:raise AssertionError(label)
 checks.append(label)
def inventory(path):return pc.inventory(path,max_bytes=64*1024**2,max_files=4000,max_entries=8000)
def forbidden(*args,**kwargs):raise RuntimeError('review forbids subprocess execution')
roots=[ROOT/'.runs'/f'placement-pruning-controls-{i:03d}' for i in range(1,5)]+[readonly]
before={str(x.relative_to(ROOT)):inventory(x) for x in roots}
record=f.read_json(run/'result.json');readback=f.read_json(readonly/'result.json');protocol=f.read_json(run/'code/experiments/placement_pruning_controls_v1/PROTOCOL.json')
must(record['status']=='failed' and record['accepted'] is False and record['controls_passed'] is False and record['observations_complete'] is False,'original004failure retained')
must(readback['status']=='readback_passed' and readback['native_reexecuted'] is False and readback['original_controller_status']=='failed','separate readback scope')
must(readback['original_run_inventory']==inventory(run),'root readback exact original run witness')
must(p.sha(ROOT/'.runs/readback-placement-pruning-controls-004.py')==readback['readback_script_sha256'],'root readback script binding')
must(p.sha(ROOT/'experiments/placement_pruning_controls_v1/driver.py')==readback['predicate_source_sha256'],'corrected predicate binding')
for rel,pins in protocol['preserved_prefixes'].items():must(inventory(ROOT/rel)==pins,'preserved prefix '+rel)
for rel,pins in protocol['input_trees'].items():must(inventory(ROOT/rel)==pins,'original source tree '+rel)
must(p.sha(run/'code/experiments/placement_pruning_controls_v1/PROTOCOL.json')==record['protocol_sha256'],'actual004 protocol binding')
must(inventory(run/'code')==record['code_inventory'],'controller code inventory')
for rel,digest in record['runtime_sources'].items():must(p.sha(run/'code'/rel)==digest,'runtime code '+rel)
for case,hashes in record['source_hashes'].items():
 source=run/'sources'/case/'fixture.kicad_pcb';must(inventory(source.parent)==hashes,'immutable derived source '+case)
 must(pc.read_bytes(source)==control.derive(pc.read_bytes(control.BASE/'smoke.kicad_pcb'),case),'exact derived source recipe '+case)
 must(p.sha(source.with_suffix('.kicad_pro'))==p.sha(control.TEMPLATE/'fixture.kicad_pro'),'unchanged inherited project '+case)
 project=f.read_json(source.with_suffix('.kicad_pro'));ignored=sorted(k for k,v in project['board']['design_settings']['rule_severities'].items() if v=='ignore')
 must(ignored==['footprint_filters_mismatch','footprint_type_mismatch','missing_courtyard','npth_inside_courtyard','pth_inside_courtyard'],'five inherited ignore choices '+case)

arm_results=[];case_results=[]
with patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden):
 for arm in record['arms']:
  receipt=Path(arm['receipt']);data=f.read_json(receipt);fresh=p.check_result(receipt)
  must(p.sha(receipt)==arm['result_sha256'],'actual arm receipt '+arm['arm'])
  must(data['accepted'] is True and data['status']=='routing_accepted' and data['native']==arm['native'] and data['metrics']==arm['metrics'],'actual arm summary '+arm['arm'])
  must(fresh==next(x for x in readback['checked_arm_receipts'] if x['candidate']==data['candidate']),'root/independent arm readback '+arm['arm'])
  must(len(data['native']['ignored_checks'])==7,'seven effective native ignores '+arm['arm'])
  board=sx.read(Path(data['candidate']));metrics=data['metrics'];length=sum(s._length(x) for x in p.routes(board))
  must(not any(x[0]=='arc' for x in p.routes(board)) and abs(length-metrics['track_length_mm'])<1e-9,'independent segment length '+arm['arm'])
  must(sum(x[0]=='via' for x in p.routes(board))==metrics['vias']==0,'independent via count '+arm['arm'])
  arm_results.append({'arm':arm['arm'],'receipt_sha256':p.sha(receipt),'source_sha256':p.sha(Path(data['source'])),'candidate_sha256':data['candidate_sha256'],'native_report_sha256':data['native_report_sha256'],'input_policy':data['input_policy'],'metrics':metrics,'native_counts':{k:data['native'][k] for k in ('opens','blocking','warnings','exclusions')},'budget_seconds':data['budget_seconds'],'wall_seconds':data['wall_seconds'],'total_cpu_seconds':data['total_cpu_seconds'],'reused_completed_control':arm.get('reused_completed_control',False)})
 for row in record['cases']:
  case=row['case'];basis=ROOT/'.runs/placement-pruning-controls-002/run/tuned' if case=='redundant' else run/'necessary_tuned'
  basis_record=f.read_json(basis/'result.json');source=Path(basis_record['source']);original=p.preflight(source);hashes=inventory(source.parent);nets=s.zone_net_ids(original)
  parent_recipe,recipe=control.bridge_parent(sx.read(Path(basis_record['candidate'])),nets)
  must(recipe==row['parent_recipe'],'exact authored bridge recipe '+case)
  parent,pnative,pmetrics=ps.check_candidate_stage(Path(row['parent']['candidate']).parent.parent,row['parent'],original,hashes,basis,parent_recipe)
  deletion=ps.deletion(parent,row['proposal'],nets)
  candidate,native,metrics=ps.check_candidate_stage(Path(row['deletion']['candidate']).parent.parent,row['deletion'],original,hashes,basis,deletion)
  parent_tree=sx.read(parent);child_tree=sx.read(candidate)
  must(p.immutable(parent_tree)==p.immutable(original)==p.immutable(child_tree),'original-design preservation witness '+case)
  removed=[x for x in p.routes(parent_tree) if x not in p.routes(child_tree)]
  must(len(removed)==1 and s.route_id(removed[0])==row['parent_recipe']['added_bridge_route_id'],'exact single bridge removed '+case)
  must(s._length(removed[0])==30 and sx.one(removed[0],'net')[1]=='"GND"' and sx.one(removed[0],'layer')[1]=='"B.Cu"','bridge length/net/layer '+case)
  must([x for x in p.routes(parent_tree) if x not in removed]==p.routes(child_tree),'all other routes unchanged '+case)
  must(pmetrics['track_length_mm']-metrics['track_length_mm']==30 and metrics['vias']==pmetrics['vias']==0,'exact witness length/via delta '+case)
  passed,targets=control.control_observation(case,pnative,native,pmetrics,metrics);must(passed,'corrected actual control predicate '+case)
  expected=next(x for x in readback['observations'] if x['case']==case)
  must(native==expected['native'] and pnative==expected['parent_native'] and targets==expected['targeted_findings'] and pmetrics==expected['parent_metrics'] and metrics==expected['metrics'] and p.sha(candidate)==expected['candidate_sha256'],'corrected root/independent case observation '+case)
  raw=f.read_json(candidate.parent.parent/'final-drc.json')
  if case=='necessary':
   must(len(raw['unconnected_items'])==1 and raw['violations']==[] and raw['schematic_parity']==[],'raw exact negative population')
   finding=raw['unconnected_items'][0]
   must('excluded' not in finding and finding['severity']=='error' and finding['type']=='unconnected_items','optional excluded field absent in actual raw error')
   must({x['uuid'] for x in finding['items']}=={control.OUTSIDE_PAD,control.ZONE_UUID},'actual negative exact zone/J6 UUID pair')
   must(native['opens']==1 and not p.native_accepted(native) and row['passed'] is False,'original necessary negative remains invalid/controllerfailed')
  else:must(native['opens']==0 and p.native_accepted(native) and row['passed'] is True,'actual redundant deletion remains native valid')
  case_results.append({'case':case,'original_controller_passed':row['passed'],'corrected_predicate_passed':passed,'parent_candidate_sha256':p.sha(parent),'candidate_sha256':p.sha(candidate),'native_report_sha256':p.sha(candidate.parent.parent/'final-drc.json'),'native_counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'parent_metrics':pmetrics,'metrics':metrics,'targeted_findings':targets})

# Retained prefix process entries must be the same actual files, not invented
# costs. This check is independent of top-level controller summary counters.
step_ids=[];process_kind=Counter();child=monitor=step_wall=0.;drc_count=0
for step in record['steps']:
 folder=Path(step['cwd']);name=step['name'];process=f.read_json(folder/(name+'-process.json'))
 must(all(step.get(k)==v for k,v in process.items()),'retained process contents '+str(folder.relative_to(ROOT))+'/'+name)
 must(step['argv'][:len(f.SANDBOX)]==f.SANDBOX,'network denied actual worker '+str(folder.relative_to(ROOT))+'/'+name)
 must(step['status'] in ('success','nonzero_exit') and step['cleanup_complete'] is True and step['log_truncated'] is False,'finished worker '+str(folder.relative_to(ROOT))+'/'+name)
 must(pc.read_bytes(Path(step['log']),1024**2).__len__()==step['log_bytes'],'exact worker log bytes '+str(folder.relative_to(ROOT))+'/'+name)
 for field in ('cpu_seconds','monitor_cpu_seconds','wall_seconds'):must(type(step[field]) in (int,float) and math.isfinite(step[field]) and step[field]>=0,'finite cost '+str(folder.relative_to(ROOT))+'/'+name+'/'+field)
 child+=step['cpu_seconds'];monitor+=step['monitor_cpu_seconds'];step_wall+=step['wall_seconds'];step_ids.append((str(folder),name));process_kind[step['argv'][len(f.SANDBOX)]]+=1
 if name.endswith('-drc'):
  binding=f.read_json(folder/(name+'-binding.json'));native=f.check_drc_stage(folder,{'steps':record['steps']},name,Path(binding['source']),Path(binding['input']),binding['saved'],binding['before']);drc_count+=1
  must(step['exit_code']==(5 if native['findings'] else 0),'DRC actual exit/findings '+str(folder.relative_to(ROOT))+'/'+name)
must(len(step_ids)==len(set(step_ids)),'no duplicated charged process entries')
must(abs(child-record['child_step_cpu_seconds'])<1e-9 and monitor==record['monitor_cpu_seconds'],'full prefix worker cost sums')
must(step_wall<=record['wall_seconds'] and child+monitor<=record['total_cpu_seconds'],'worker costs included by enclosing totals')
old=f.read_json(ROOT/'.runs/placement-pruning-controls-003/run/result.json')
must(record['steps'][:len(old['steps'])]==old['steps'],'all prior successful/failed workers retained')
current_files={str(path.relative_to(run)):p.sha(path) for path in run.rglob('*-process.json')}
new_steps=record['steps'][len(old['steps']):]
must({str(Path(x['cwd'])/(x['name']+'-process.json')) for x in new_steps}=={str(run/name) for name in current_files},'complete new worker file population accounted')

prefix=[];full_wall=full_cpu=0.
for i in range(1,5):
 outer=ROOT/'.runs'/f'placement-pruning-controls-{i:03d}';execution=f.read_json(outer/'execution.json');full_wall+=execution['wall_seconds'];full_cpu+=execution['full_cpu_seconds']
 must(execution['process']['cleanup_complete'] is True and execution['process']['status']=='nonzero_exit','old outer failure retained '+str(i))
 must(p.sha(outer/'command.log')==execution['log_sha256'],'outer log binding '+str(i))
 result=f.read_json(outer/'run/result.json') if (outer/'run/result.json').exists() else None
 if result:must(result['status']=='failed' and result['controls_passed'] is False,'old controller failure retained '+str(i))
 prefix.append({'id':f'{i:03d}','status':result['status'] if result else 'pre-native interface failure/no controller receipt','error':result.get('error') if result else None,'execution_sha256':p.sha(outer/'execution.json'),'outer_wall_seconds':execution['wall_seconds'],'outer_full_cpu_seconds':execution['full_cpu_seconds'],'step_count':len(result.get('steps',[])) if result else 0})
must(abs(record['resumed_prefix']['wall_seconds']-sum(x['outer_wall_seconds'] for x in prefix[:3]))<1e-9,'exact all failed/successful prefix wall charged')
must(abs(record['resumed_prefix']['total_cpu_seconds']-sum(x['outer_full_cpu_seconds'] for x in prefix[:3]))<1e-9,'exact all failed/successful prefix CPU charged')
must(full_wall<record['budget_seconds']==180 and full_cpu<record['cpu_budget_seconds']==180,'whole outer execution series within shared control caps')
core=f.read_json(run/'C/result.json');inc=f.read_json(run/'C/incumbent/result.json')
must(core['improvements']==1 and inc['metrics']['track_length_mm']==90 and core['metrics']['track_length_mm']==60 and len(core['trials'])==1 and core['trials'][0]['accepted'] is True,'actual ordinary C own-incumbent pruning control')
must(core['reference_routes_used_for_selection'] is False and core['novel_routing_algorithm_claim'] is False,'C narrow algorithm/reference scope')
must(all(record[k] is False for k in ('routing_quality_gain_claim','production_support_extended','family_comparison_eligible','physical_electrical_validation')),'controller limitations remain explicit')
for key,path in zip(before,roots):must(inventory(path)==before[key],'review leaves original evidence unchanged '+key)
result={'schema':1,'status':'audit_passed','native_reexecuted':False,'subprocess_executed':False,'original004status':'failed','guard_count':len(checks),'guards':checks,'arm_results':arm_results,'case_results':case_results,'prefix':prefix,'process_population':{'total_unique_processes':len(step_ids),'DRC_stages':drc_count,'executable_counts':dict(process_kind),'summed_step_wall_seconds':step_wall,'summed_worker_cpu_seconds':child,'summed_monitor_cpu_seconds':monitor},'series_outer_wall_seconds':full_wall,'series_outer_full_cpu_seconds':full_cpu,'root_readback_wall_seconds':readback['wall_seconds'],'root_readback_cpu_seconds':readback['full_cpu_seconds'],'series_plus_root_readback_wall_seconds':full_wall+readback['wall_seconds'],'series_plus_root_readback_full_cpu_seconds':full_cpu+readback['full_cpu_seconds'],'audit_wall_seconds':time.monotonic()-start,'audit_parent_cpu_seconds':time.process_time()-cpu,'bindings':{'original004receipt':p.sha(run/'result.json'),'root_readback':p.sha(readonly/'result.json'),'root_readback_script':readback['readback_script_sha256'],'actual004protocol':record['protocol_sha256'],'current_predicate':readback['predicate_source_sha256'],'source_inventories':record['source_hashes'],'readonly_root_inventories':before},'scope':'Owned engineered integration/native positive and required-copper negative only; no matched B0/B1/B2/C quality or independent-family gain.'}
p.save_json(HERE/'audit.json',result)
print(json.dumps({k:result[k] for k in ('status','native_reexecuted','guard_count','process_population','series_outer_wall_seconds','series_outer_full_cpu_seconds','audit_wall_seconds')}))
