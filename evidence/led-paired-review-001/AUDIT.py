"""Read-only actual LED comparison audit using existing validators; no workers."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess,sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,strategy as s
from scripts import experiment_portfolio as m,experiment_paired as paired
RUN=ROOT/'.runs/push-button-led-native-paired-complete-sch-001/run'
QUAL=ROOT/'.runs/push-button-led-native-paired-complete-sch-002-qualification'
SPEC=ROOT/'.runs/push-button-led-native-paired-complete-sch-001-protocol.json'
AMEND=ROOT/'.runs/push-button-led-native-paired-complete-sch-002-qualification-protocol.json'
FAIL=ROOT/'.runs/push-button-led-native-paired-complete-sch-001-qualification-prelaunch-failure'
def read(path):return f.read_json(path)
def require(value,message):
 if not value:raise ValueError(message)
def forbidden(*args,**kwargs):raise AssertionError('Audit may not launch native/JVM/Git/network/subprocesses')
def inventory(path):return pc.inventory(path,max_bytes=96*1024**2,max_files=16000,max_entries=32000,with_directories=True)
def digest(value):return hashlib.sha256(f.canonical(value).encode()).hexdigest()
inputs={str(x):inventory(x) for x in [RUN.parent,QUAL,FAIL]}
spec=read(SPEC);amend=read(AMEND);protocol=read(RUN/'protocol.json');freeze=protocol['freeze'];source=Path(protocol['source'])
source_before=pc.inventory(source.parent);original=p.preflight(source)
summary=read(RUN/'paired-summary.json');outer=read(RUN.parent/'execution.json');qualification=read(QUAL/'result.json');execution=read(QUAL/'execution.json');failure=read(FAIL/'failure.json')
require(source_before==freeze['source_hashes'],'source snapshot/freeze differs')
require(summary['status']=='completed' and summary['protocol_sha256']==p.sha(RUN/'protocol.json'),'paired index invalid')
require(protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'caps changed')
require(protocol['arm_order']==[x['id'] for x in summary['results']]==['B0','B1','B2_portfolio','C_feedback'],'population changed')
require(freeze['tools']['git_head']==spec['git_head']=='31656e1f4579ef194b1ada74b44bd8377fd483b2','actual code checkpoint differs')
for relative,sha in freeze['files_sha256'].items():
 require(p.sha(RUN/'frozen-code'/relative)==sha,'retained frozen source differs: '+relative)
 require(p.sha(ROOT/relative)==sha,'current production differs: '+relative)
for relative,sha in freeze['tools']['implementation_sha256'].items():require(p.sha(ROOT/relative)==sha,'current validator differs: '+relative)
require(p.sha(SPEC)==outer['prospective_protocol_sha256']==qualification['prospective_protocol_sha256']==amend['unchanged_native_protocol_sha256'],'prospective binding differs')
require(p.sha(AMEND)==qualification['qualification_amendment_sha256'],'amendment changed')
require(p.sha(FAIL/'failure.json')==amend['prior_failure_sha256'] and failure['native_calls']==0,'old failed audit changed')
require(p.sha(ROOT/'.runs/qualify-push-button-led-native-paired-complete-sch-002.py')==amend['controller_sha256']==qualification['controller_sha256'],'corrective controller differs')
require(p.sha(ROOT/'.runs/qualify-push-button-led-native-paired-complete-sch-001.py')==amend['failed_controller_sha256']==failure['controller_sha256'],'first failed controller differs')
require(p.sha(RUN/'paired-summary.json')==qualification['paired_summary_sha256'] and p.sha(RUN.parent/'execution.json')==qualification['outer_execution_sha256'],'final qualification input differs')
require(p.sha(QUAL/'result.json')==execution['result_sha256'] and qualification['status']=='completed' and qualification['comparison_eligible'] is True and qualification['accepted'] is False,'corrective qualification not eligible')
require(qualification['new_native_execution'] is False and qualification['physical_electrical_validation'] is False,'claims widened')
require(max(execution['wall_seconds'],execution['full_cpu_seconds'])<execution['fixed_charge_seconds']==5,'corrective actual audit cap differs')
require(outer['log_sha256']==p.sha(RUN.parent/'command.log') and outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False,'outer worker evidence differs')
require(outer['process']['log_bytes']==(RUN.parent/'command.log').stat().st_size,'outer log bytes differ')
records={};checks={};unique_processes={};native_counts={};warning_signatures={};ignored={}
leaves=[('B0','B0'),('B1','B1'),('B2_default','B2_portfolio/01-via_default'),('B2_low','B2_portfolio/02-via_low'),('B2_high','B2_portfolio/03-via_high'),('C_incumbent','C_feedback/incumbent'),('C_final','C_feedback')]
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
 for name,relative in leaves:
  folder=RUN/relative;d=read(folder/'result.json');records[name]=d
  if name!='B0':checks[name]=p.check_result(folder/'result.json')
  else:
   try:p.check_result(folder/'result.json')
   except p.Rejected as exc:checks[name]={'rejected':str(exc)}
   else:raise ValueError('invalid B0 accepted')
  require(d['source_hashes']==source_before and d['tools']==freeze['tools'],'leaf source/tool differs')
  require(pc.inventory(folder/'snapshot')==source_before,'snapshot changed')
  candidate=Path(d['candidate']);tree=sx.read(candidate)
  require(p.immutable(tree)==p.immutable(original),'immutable design changed')
  protected=p.protected_for_record(d,original)
  require(all(x in p.routes(tree) for x in protected),'protected route missing')
  p.verify_candidate_files(candidate,source_before,d['candidate_sha256']);p.check_protected_import(folder,d,original,candidate,protected);p.check_resource_accounting(d)
  native=p.parse_report(folder/'final-drc.json',source.name)
  require(native==d['native'] and p.sha(folder/'final-drc.json')==d['native_report_sha256'],'raw final DRC differs')
  before=dict(source_before);before[source.name]=d['candidate_sha256']
  require(f.check_drc_stage(folder,d,'final-drc',candidate,folder/'final-drc-input'/source.name,False,before,schematic_parity=True,sandboxed=False)==native,'full original-rule/parity native differs')
  counts=[native[k] for k in ('opens','blocking','warnings','exclusions')]
  require(counts==([0,4,7,0] if name=='B0' else [0,0,7,0]),'native counts differ')
  require(d['whole_project_drc_clean'] is False and d['metrics']==read(folder/'metrics.json'),'warnings/metrics changed')
  native_counts[name]=counts
  warning_signatures[name]=digest([x for x in native['findings'] if x['severity']=='warning']);ignored[name]=digest(native['ignored_checks'])
  for step in d['steps']:
   process=Path(step['cwd'])/(step['name']+'-process.json');retained=read(process)
   require(all(step.get(k)==v for k,v in retained.items()),'retained process/history differs')
   require(retained['status'] in ('success','nonzero_exit') and retained['cleanup_complete'] is True and retained['log_truncated'] is False,'worker failed/cancelled/truncated')
   require(Path(retained['log']).stat().st_size==retained['log_bytes'],'process log size differs')
   unique_processes[str(process)]={'sha256':p.sha(process),'stage':step['name'],'argv_sha256':digest(retained['argv']),'wall_seconds':retained['wall_seconds'],'cpu_seconds':retained['cpu_seconds'],'status':retained['status'],'exit_code':retained['exit_code']}
 portfolio=read(RUN/'B2_portfolio/portfolio-summary.json')
 require([r['id'] for r in portfolio['trials']]==list(m.VARIANTS) and all(r['eligible'] for r in portfolio['trials']),'B2 trials omitted')
 checks['portfolio']=paired.verify_portfolio(RUN/'B2_portfolio',portfolio,source,freeze)['accepted']
 require(checks['portfolio'] and portfolio['selected']['id']==min(portfolio['trials'],key=m.rank)['id']=='via_default','B2 selection changed')
 c=records['C_final'];inc=records['C_incumbent'];trialfolder=RUN/'C_feedback/trials/trial-0000';trial=read(trialfolder/'result.json')
 require(len(c['trials'])==c['improvements']==1 and trial['accepted'] is True and trial['status']=='improvement_validated','pruning history differs')
 require(c['incumbent']['receipt']==str(RUN/'C_feedback/incumbent/result.json') and trial['base_candidate_sha256']==p.sha(Path(inc['candidate'])),'free/rebased incumbent')
 nets=s.zone_net_ids(original);protected=p.protected_for_record(c,original)
 require(trial['proposal']==s.proposals(sx.read(inc['candidate']),nets,protected,True)[0],'proposal selection replay differs')
 deleted=s.delete_routes(sx.read(inc['candidate']),trial['proposal']['route_ids'],nets,protected)
 candidate=trialfolder/'candidate'/source.name;refill=trialfolder/'refill'/source.name
 before=dict(source_before);before[source.name]=hashlib.sha256((sx.dump(deleted)+'\n').encode()).hexdigest()
 f.check_drc_stage(trialfolder,trial,'refill-drc',refill,refill,True,before,sandboxed=False)
 require((sx.dump(p.transplant_fill(deleted,sx.read(refill)))+'\n').encode()==pc.read_bytes(candidate),'saved-refill reconstruction differs')
 before[source.name]=trial['candidate_sha256']
 native=f.check_drc_stage(trialfolder,trial,'final-drc',candidate,trialfolder/'final-drc-input'/source.name,False,before,schematic_parity=True,sandboxed=False)
 require(native==trial['native'] and p.sha(trialfolder/'final-drc.json')==trial['native_report_sha256'],'fresh trial native differs')
 require(p.immutable(sx.read(candidate))==p.immutable(original) and p.sha(candidate)==trial['candidate_sha256']==c['candidate_sha256'],'trial/final/source design differs')
 require(trial['metrics']==c['metrics'] and s._warning_signatures(native)==s._warning_signatures(inc['native']),'pruning quality/warnings changed')
 require(Counter(sx.dump(r) for r in p.routes(sx.read(candidate)))<=Counter(sx.dump(r) for r in p.routes(sx.read(inc['candidate']))),'pruning added/changed copper')
 for step in trial['steps']:
  process=Path(step['cwd'])/(step['name']+'-process.json');retained=read(process)
  require(all(step.get(k)==v for k,v in retained.items()) and retained['cleanup_complete'] is True and retained['log_truncated'] is False,'trial process binding failed')
  require(Path(retained['log']).stat().st_size==retained['log_bytes'],'trial log size differs')
  unique_processes[str(process)]={'sha256':p.sha(process),'stage':step['name'],'argv_sha256':digest(retained['argv']),'wall_seconds':retained['wall_seconds'],'cpu_seconds':retained['cpu_seconds'],'status':retained['status'],'exit_code':retained['exit_code']}
require(len(set(warning_signatures.values()))==len(set(ignored.values()))==1,'warnings or ignored checks changed')
require(records['C_incumbent']['candidate_sha256'] not in {records[x]['candidate_sha256'] for x in ['B1','B2_default','B2_low','B2_high']},'incumbent candidate reused')
require(p.sha(RUN/'B0/native.dsn')==p.sha(RUN/'B0/task.dsn'),'stock representation altered')
rows={r['id']:r for r in summary['results']};costs={}
for row in qualification['results']:
 old=rows[row['id']]
 require(abs(old['charged_wall_seconds']-old['invocation_wall_seconds']-summary['shared_overhead_wall_seconds'])<1e-6,'paired shared wall omitted')
 require(abs(old['charged_cpu_seconds']-old['invocation_cpu_seconds']-summary['shared_overhead_cpu_seconds'])<1e-6,'paired shared CPU omitted')
 wall=old['charged_wall_seconds']+max(0,outer['wall_seconds']-summary['batch_wall_seconds'])+5+5+spec['shared_original_qualification_cost']['wall_seconds']
 cpu=old['charged_cpu_seconds']+max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds'])+5+5+spec['shared_original_qualification_cost']['full_cpu_seconds']
 require(abs(wall-row['charged_wall_seconds'])<1e-6 and abs(cpu-row['charged_full_cpu_seconds'])<1e-6 and max(wall,cpu)<120,'complete equal charges/caps differ')
 costs[row['id']]={'wall_seconds':wall,'full_cpu_seconds':cpu,'accepted':row['accepted']}
require(p.sha(ROOT/spec['shared_original_qualification_cost']['execution_path'])==spec['shared_original_qualification_cost']['execution_sha256'],'source qualification prefix changed')
require(pc.inventory(source.parent)==source_before and all(inventory(Path(x))==v for x,v in inputs.items()),'evidence/source changed during readback')
result={'schema':1,'scope':'Read-only retained actual native validation; no native/JVM/Git/network execution. Existing shared validators, no cache/Git identity call.','git_head':freeze['tools']['git_head'],'checks':checks,'native_counts':native_counts,'candidate_sha256':c['candidate_sha256'],'B1_mm':records['B1']['metrics']['track_length_mm'],'B2_selected_mm':portfolio['selected']['length_mm'],'C_mm':c['metrics']['track_length_mm'],'C_vias':c['metrics']['vias'],'gain_vs_B2_mm':portfolio['selected']['length_mm']-c['metrics']['track_length_mm'],'deleted_routes':len(trial['proposal']['route_ids']),'deletion_types':dict(Counter(r[0] for r in p.routes(sx.read(inc['candidate'])) if s.route_id(r) in set(trial['proposal']['route_ids']))),'protected_source_routes':len(protected),'warning_signature_sha256':warning_signatures,'ignored_checks_sha256':ignored,'costs':costs,'actual_outer_wall_seconds':outer['wall_seconds'],'actual_outer_full_cpu_seconds':outer['full_cpu_seconds'],'failed_audit_native_calls':failure['native_calls'],'failed_audit_exact_cpu_measured':failure['child_cpu_directly_recorded'],'corrective_audit_observed':execution,'whole_project_clean':False,'comparison_eligible':True,'physical_electrical_validation':False,'raw_run_inventory_sha256':digest(inputs[str(RUN.parent)]),'unique_process_records':unique_processes,'scope_limits':['One exposed 7-component development/support-control family, not heldout or general superiority.','Seven library warnings and five original ignored checks remain. No field/parity waiver was needed.','Raw outer stopwatch starts after supervisor imports and ends before final execution write; early/late overhead not exact. No speedup claim.','Failed first audit has no exact child CPU record; equal conservative 5-second charge is a declared allowance.']}
print(json.dumps(result,indent=2))
