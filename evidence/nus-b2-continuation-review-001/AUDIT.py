"""Read-only audit of completed continuation using existing shared validators."""
import time,resource
START=time.monotonic();START_CPU=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime
from pathlib import Path
from collections import Counter
import copy,hashlib,json,subprocess,sys
from unittest.mock import patch
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,schematic_field_evidence as fields
from scripts import experiment_portfolio as portfolio
OLD=ROOT/'.runs/nus-native-paired-002/run';NEW=ROOT/'.runs/nus-b2-portfolio-continuation-001';PORT=NEW/'portfolio'
def read(path):return f.read_json(path)
def require(value,message):
    if not value:raise ValueError(message)
def sha_value(value):return hashlib.sha256(f.canonical(value).encode()).hexdigest()
def inventory(path):return pc.inventory(path,max_bytes=96*1024**2,max_files=16000,max_entries=32000)
def forbidden(*args,**kwargs):raise AssertionError('Review cannot execute subprocess/native/JVM/Git/network')
old_before=inventory(OLD);new_before=inventory(NEW);original_review=read(ROOT/'.runs/nus-paired-002-review-001/actual-audit.json')
require(hashlib.sha256(json.dumps(old_before,sort_keys=True).encode()).hexdigest()==original_review['actual_run_inventory_sha256'],'original failed paired evidence changed since frozen review')
summary=read(PORT/'portfolio-summary.json');protocol=read(PORT/'protocol.json');execution=read(NEW/'execution.json')
prospective=read(ROOT/'.runs/nus-b2-portfolio-continuation-001-protocol.json');source=Path(protocol['source']);original=p.preflight(source)
source_before=pc.inventory(source.parent);frozen=protocol['freeze'];oldprotocol=read(OLD/'B2_portfolio/protocol.json')
require(protocol['schema']==2 and summary['schema']==2 and summary['kind']=='experimental_baseline_portfolio_resume','continuation schema differs')
require(summary['protocol_sha256']==p.sha(PORT/'protocol.json'),'summary protocol hash differs')
require(execution['protocol_sha256']==p.sha(ROOT/'.runs/nus-b2-portfolio-continuation-001-protocol.json'),'prospective protocol hash differs')
require(source_before==frozen['source_hashes']==oldprotocol['freeze']['source_hashes']==original_review['source_inventory'],'source freeze changed')
require(frozen['tools']==prospective['tools'] and frozen['tools']['git_head']=='d610a2ccc98f32b0a12444a1e5e835004ff125c0','continuation tool/HEAD binding differs')
portfolio.compatible_resume_freeze(oldprotocol['freeze'],frozen)
require(pc.inventory(PORT/'frozen-code')==frozen['files_sha256'],'fresh frozen code changed')
require(pc.inventory(OLD/'B2_portfolio/frozen-code')==oldprotocol['freeze']['files_sha256'],'old frozen code changed')
require(all(p.sha(ROOT/rel)==digest for rel,digest in frozen['files_sha256'].items()),'current source differs from actual continuation freeze')
for name,digest in frozen['tools']['files'].items():
    h=hashlib.sha256()
    with Path(name).open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    require(h.hexdigest()==digest,'actual tool differs from pinned continuation: '+name)
require([row['id'] for row in summary['trials']]==list(portfolio.VARIANTS),'fixed trial population/order differs')
require(set(x.name for x in PORT.iterdir())=={'frozen-code','protocol.json','portfolio-summary.json','02-via_low','03-via_high'},'unexpected trial/republication artifacts')
require(summary['status']=='completed' and summary['comparison_eligible'] is True and summary['selected']['id']=='via_default','portfolio selection differs')
records={};checks={};details={}
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
    portfolio.verify_resume_basis(protocol['resume'])
    basis=portfolio.resume_basis(Path(prospective['resume_plan']),prospective['resume_plan_sha256'],source,frozen,summary['cpu_budget_seconds'],'nus-usb-led',None)
    require(basis==protocol['resume'],'stored continuation basis differs from independently derived prefix')
    for row in summary['trials']:
        folder=Path(row['result']).parent;data=read(Path(row['result']));candidate=Path(data['candidate']);records[row['id']]=data
        require(row['result_sha256']==p.sha(Path(row['result'])),'row receipt hash differs')
        expected_freeze=portfolio.trial_freeze(protocol,row)
        require(data['tools']==expected_freeze['tools'] and data['source_hashes']==source_before,'per-row original freeze differs')
        require(data['budget_seconds']==data['cpu_budget_seconds']==row['assigned_seconds'],'row allowance differs')
        require(row['invocation_wall_seconds']<=row['assigned_seconds'] and row['invocation_cpu_seconds']<=row['assigned_seconds'],'row exceeded allowance')
        require(pc.inventory(folder/'snapshot')==source_before,'snapshot changed')
        p.verify_candidate_files(candidate,source_before,data['candidate_sha256'])
        require(p.immutable(sx.read(candidate))==p.immutable(original),'original nonrouting design changed')
        protected=p.protected_for_record(data,original)
        require(all(route in p.routes(sx.read(candidate)) for route in protected),'protected route lost')
        p.check_protected_import(folder,data,original,candidate,protected)
        task=copy.deepcopy(original);task[:]=[node for node in task if not isinstance(node,list) or not node or node[0] not in p.ROUTES or p.locked(node)]
        for zone in sx.children(task,'zone'):zone[:]=[node for node in zone if not isinstance(node,list) or not node or node[0] not in p.DERIVED_ZONE]
        require(hashlib.sha256((sx.dump(task)+'\n').encode()).hexdigest()==data['task_sha256'],'original task replay differs')
        imported=p.transplant_routes(task,sx.read(folder/'imported.kicad_pcb'))
        require((sx.dump(imported)+'\n').encode()==pc.read_bytes(folder/'pour-before-refill.kicad_pcb'),'retained SES import/task reconstruction differs')
        source_native=f.check_drc_stage(folder,data,'source-drc',folder/'snapshot'/source.name,folder/'source-drc-input'/source.name,False,source_before,sandboxed=False)
        require(source_native==data['source_drc'],'source native summary differs')
        p.check_pour_evidence(folder,data,original,candidate)
        expected=dict(source_before);expected[source.name]=data['candidate_sha256']
        native=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/source.name,False,expected,schematic_parity=True,sandboxed=False)
        require(native==data['native'] and p.sha(folder/'final-drc.json')==data['native_report_sha256'],'raw native evidence differs')
        require(data['metrics']==read(folder/'metrics.json'),'native metrics differ')
        require(data['whole_project_drc_clean'] is False,'warnings hidden')
        p.check_preferences_record(folder,data);p.check_minimum_width_record(data,folder);p.check_resource_accounting(data)
        expected_engine=p.engine_profile_settings('tuned',data['engine_budget']['remaining_outer_wall_seconds_at_assignment'],strict_class_targets=True,scoring_variant=row['id'])
        require(all(data['engine_budget'].get(key)==value for key,value in expected_engine.items()),'predeclared scoring/profile differs')
        f.process_check(folder,data,'engine',p.engine_argv(folder,data['engine_budget']['argv']))
        for step in data['steps']:
            process=read(Path(step['cwd'])/(step['name']+'-process.json'))
            require(all(step.get(key)==value for key,value in process.items()),'raw process/history differs')
            require(process['cleanup_complete'] is True and process['status'] in {'success','nonzero_exit'} and process['log_truncated'] is False,'failed process concealed')
            require(Path(process['log']).stat().st_size==process['log_bytes'],'process log length changed')
        if row['eligible']:
            checks[row['id']]=portfolio.verify_row(row,source,expected_freeze)
            require(p.native_rejection_reasons(native)==[],'eligible row native reasons reject')
        else:
            require(row['id']=='via_low' and row['accepted_in_trial_receipt'] is False and data['accepted'] is False and data['status']=='drc_rejected','low rejection hidden')
            try:p.check_result(Path(row['result']))
            except p.Rejected as exc:checks[row['id']]={'rejected':str(exc)}
            else:raise ValueError('invalid low candidate passes central checker')
        details[row['id']]={'candidate_sha256':data['candidate_sha256'],'native_report_sha256':data['native_report_sha256'],'receipt_sha256':row['result_sha256'],'status':data['status'],'native_counts':{key:native[key] for key in ['opens','blocking','warnings','exclusions']},'metrics':data['metrics'],'steps':len(data['steps']),'native_worker_count':sum(step['name']!='engine' for step in data['steps']),'warning_types':dict(Counter(x['type'] for x in native['findings'] if x['severity']=='warning')),'opens':[x for x in native['findings'] if x['type']=='unconnected_items'],'assigned_seconds':row['assigned_seconds'],'invocation_wall_seconds':row['invocation_wall_seconds'],'invocation_cpu_seconds':row['invocation_cpu_seconds']}
    c=read(OLD/'C_feedback/result.json');b1=read(OLD/'B1/result.json')
    checks['C']=p.check_result(OLD/'C_feedback/result.json');checks['B1']=p.check_result(OLD/'B1/result.json')
    require(c['candidate_sha256']==original_review['candidate_sha256'],'previously audited C candidate changed')
    chosen=min([row for row in summary['trials'] if row['eligible']],key=portfolio.rank)
    require(summary['pareto_frontier']==portfolio.frontier(summary['trials'])==['via_default'],'frontier differs')
    require(all(summary['selected'][key]==chosen[key] for key in ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm')),'selection binding differs')
    signatures=lambda d:Counter(f.canonical(x) for x in d['native']['findings'] if x['severity']=='warning')
    require(signatures(c)==signatures(b1)==signatures(records['via_default'])==signatures(records['via_high'])==signatures(records['via_low']),'warning findings altered')

old_summary=read(OLD/'B2_portfolio/portfolio-summary.json')
require(old_summary['status']=='invalidated' and old_summary['comparison_eligible'] is False and old_summary['selected'] is None and len(old_summary['trials'])==1,'original failure rewritten')
require(not (OLD/'B2_portfolio/02-via_low').exists() and not (OLD/'B2_portfolio/03-via_high').exists(),'old directory received new trial')
process=execution['process'];require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False,'outer execution incomplete')
require(process['log_bytes']==(NEW/'command.log').stat().st_size,'outer log size differs')
require(process['argv'][0:3]==f.SANDBOX and process['argv'][-1]==str(PORT),'outer command sandbox/output differs')
prefix=execution['prior_entire_invocation'];require(prefix==prospective['prior_entire_invocation'],'prior prefix differs')
require(prefix['wall_seconds']==original_review['B2_full_prefix_wall_seconds'] and prefix['full_cpu_seconds']==original_review['B2_full_prefix_cpu_seconds'],'original complete prefix undercharged')
for field,a,b in [('combined_active_wall_seconds',prefix['wall_seconds'],execution['whole_new_wall_seconds']),('combined_full_cpu_seconds',prefix['full_cpu_seconds'],execution['whole_new_full_cpu_seconds'])]:require(abs(execution[field]-(a+b))<1e-8,'full foreground prefix/suffix arithmetic differs')
require(execution['whole_new_wall_seconds']>=process['wall_seconds'] and execution['whole_new_full_cpu_seconds']>=process['cpu_seconds']+process['supervisor_cpu_seconds']+process['monitor_cpu_seconds'],'foreground omits supervisor/startup')
require(execution['combined_active_wall_seconds']<=execution['same_arm_allowance_seconds']==summary['wall_budget_seconds']==summary['cpu_budget_seconds'] and execution['combined_full_cpu_seconds']<=execution['same_arm_allowance_seconds'],'continuation exceeds same allowance')
shared_wall=original_review['original_shared_wall_seconds']+original_review['original_outer_excess_wall_seconds'];shared_cpu=original_review['original_shared_cpu_seconds']+original_review['original_outer_excess_cpu_seconds']
charged={'active_wall_seconds_before_new_additive_readback':execution['combined_active_wall_seconds']+shared_wall,'full_cpu_seconds_before_new_additive_readback':execution['combined_full_cpu_seconds']+shared_cpu,'later_readback_publication_charge_pending':True}
require(charged['active_wall_seconds_before_new_additive_readback']<120 and charged['full_cpu_seconds_before_new_additive_readback']<120,'full original overhead loses 120 budget')
require(inventory(OLD)==old_before and inventory(NEW)==new_before and pc.inventory(source.parent)==source_before,'audit changed input or input raced')
result={'schema':1,'status':'actual_continuation_audited_final_comparison_charge_pending','fresh_native_execution':False,'subprocess_execution':False,'original_pair_inventory_sha256':sha_value(old_before),'new_execution_inventory_sha256':sha_value(new_before),'original_failed_pair_preserved':True,'source_hashes':source_before,'current_freeze_and_actual_tools_verified':True,'details':details,'checks':checks,'budget':charged,'execution_prefix_and_suffix':{key:execution[key] for key in ['prior_entire_invocation','whole_new_wall_seconds','whole_new_full_cpu_seconds','combined_active_wall_seconds','combined_full_cpu_seconds','same_arm_allowance_seconds','calendar_gap']},'C_length_mm':c['metrics']['track_length_mm'],'B2_selected_length_mm':chosen['length_mm'],'gain_vs_B2_mm':chosen['length_mm']-c['metrics']['track_length_mm'],'vias':c['metrics']['vias'],'C_candidate_sha256':c['candidate_sha256'],'whole_project_clean':False,'claim_scope':'One exposed development family; interrupted active-budget continuation, immutable failed originals. New all-arm final readback/publication accounting still pending; no population/physical/electrical/GUI qualification.'}
result['reviewer_audit_wall_seconds_before_report_write']=time.monotonic()-START
result['reviewer_audit_cpu_seconds_before_report_write']=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime-START_CPU
(HERE/'actual-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'gain_vs_B2_mm':result['gain_vs_B2_mm'],'budget':charged,'audit_wall_seconds':result['reviewer_audit_wall_seconds_before_report_write'],'audit_cpu_seconds':result['reviewer_audit_cpu_seconds_before_report_write']},sort_keys=True))
